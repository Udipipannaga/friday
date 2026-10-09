import hashlib
import json
import secrets
import time
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Literal
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from pwdlib import PasswordHash
from sqlalchemy import select, update, func, text
from sqlalchemy.exc import IntegrityError
from . import db, providers, physics, operating, study_review
from .config import settings
from .execution import TERMINAL, event

app = FastAPI(title='FRIDAY', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.origin], allow_credentials=True,
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'X-Friday-Request'])
passwords = PasswordHash.recommended()
dummy_hash = passwords.hash(secrets.token_urlsafe(24))


@app.exception_handler(operating.DraftBlocked)
async def operating_input_error(_request: Request, exc: operating.DraftBlocked):
    return JSONResponse({'detail': str(exc)}, status_code=422)


@app.middleware('http')
async def browser_security(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('origin') != settings.origin or request.headers.get('X-Friday-Request') != '1':
            return JSONResponse({'detail': 'Request origin or CSRF header rejected.'}, status_code=403)
        if 'transfer-encoding' in request.headers or 'content-length' not in request.headers:
            return JSONResponse({'detail': 'A bounded Content-Length is required.'}, status_code=411)
        try:
            length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return JSONResponse({'detail': 'Invalid request size.'}, status_code=400)
        if length > 20000:
            return JSONResponse({'detail': 'Request too large.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers['Cache-Control'] = 'no-store'
    return response


def session():
    with db.Session() as s:
        yield s


DB = Annotated[object, Depends(session)]


def current_user(request: Request, s: DB):
    token = request.cookies.get('friday_session', '')
    row = s.get(db.SessionToken, hashlib.sha256(token.encode()).hexdigest())
    if not row or row.expires < time.time():
        raise HTTPException(401, 'Sign in to FRIDAY.')
    user = s.get(db.User, row.user_id)
    require_access(s, user)
    return user


User = Annotated[db.User, Depends(current_user)]


def is_owner(user):
    return user.email == settings.owner_email.strip().lower()


def require_access(s, user):
    if settings.registration_open or is_owner(user):
        return
    access = s.scalar(select(db.AccessRequest).where(db.AccessRequest.email == user.email))
    if not access or access.status != 'accepted':
        raise HTTPException(403, 'Owner approval is required.')


def owner_only(user):
    if not is_owner(user):
        raise HTTPException(403, 'Only the workspace owner can manage access.')


def require_owned(s, model, id, user):
    row = s.get(model, id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, 'Not found.')
    return row


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str = Field(min_length=12, max_length=128)


def throttle(s, key):
    digest = hashlib.sha256(key.encode()).hexdigest()
    window = int(time.time() // 300)
    row = s.get(db.AuthAttempt, digest)
    if not row:
        try:
            with s.begin_nested():
                s.add(db.AuthAttempt(key=digest, window=window, count=0))
                s.flush()
        except IntegrityError:
            pass
    s.execute(update(db.AuthAttempt).where(db.AuthAttempt.key == digest, db.AuthAttempt.window != window).values(window=window, count=0))
    result = s.execute(update(db.AuthAttempt).where(db.AuthAttempt.key == digest, db.AuthAttempt.count < 15).values(count=db.AuthAttempt.count + 1))
    s.commit()
    if result.rowcount != 1:
        raise HTTPException(429, 'Too many sign-in attempts. Try again in five minutes.')


def issue_session(s, user, response):
    token = secrets.token_urlsafe(32)
    lifetime = 86400 * (90 if is_owner(user) else 7)
    s.add(db.SessionToken(digest=hashlib.sha256(token.encode()).hexdigest(), user_id=user.id, expires=time.time() + lifetime))
    s.commit()
    response.set_cookie('friday_session', token, httponly=True, secure=settings.secure_cookie, samesite='strict', max_age=lifetime, path='/')
    return {'email': user.email}


@app.post('/api/auth/register', status_code=201)
def register(body: Credentials, request: Request, response: Response, s: DB):
    if not settings.registration_open:
        raise HTTPException(403, 'Registration is closed.')
    throttle(s, 'ip:' + (request.client.host if request.client else 'unknown'))
    user = db.User(email=body.email.strip().lower(), password=passwords.hash(body.password))
    s.add(user)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        raise HTTPException(409, 'Account could not be created. Try signing in.')
    return issue_session(s, user, response)


@app.post('/api/auth/login')
def login(body: Credentials, request: Request, response: Response, s: DB):
    email = body.email.strip().lower()
    throttle(s, 'ip:' + (request.client.host if request.client else 'unknown'))
    throttle(s, 'email:' + email)
    user = s.scalar(select(db.User).where(db.User.email == email))
    valid = passwords.verify(body.password, user.password if user else dummy_hash)
    if not user or not valid:
        raise HTTPException(401, 'Email or password is incorrect.')
    require_access(s, user)
    return issue_session(s, user, response)


@app.post('/api/auth/logout')
def logout(request: Request, response: Response, s: DB, user: User):
    digest = hashlib.sha256(request.cookies['friday_session'].encode()).hexdigest()
    s.delete(s.get(db.SessionToken, digest))
    s.commit()
    response.delete_cookie('friday_session', path='/')
    return {'ok': True}


@app.get('/api/me')
def me(user: User, request: Request, response: Response, s: DB):
    if is_owner(user):
        token = request.cookies['friday_session']
        row = s.get(db.SessionToken, hashlib.sha256(token.encode()).hexdigest())
        row.expires = time.time() + 86400 * 90
        s.commit()
        response.set_cookie('friday_session', token, httponly=True, secure=settings.secure_cookie,
            samesite='strict', max_age=86400 * 90, path='/')
    return {'email': user.email, 'is_owner': is_owner(user), 'jobs_today': user.quota_used if user.quota_day == int(time.time() // 86400) else 0,
        'daily_job_limit': settings.daily_jobs}


class AccessEmail(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


@app.post('/api/access/request')
def request_access(body: AccessEmail, request: Request, s: DB):
    throttle(s, 'access:' + (request.client.host if request.client else 'unknown'))
    email = body.email.strip().lower()
    existing = s.scalar(select(db.AccessRequest).where(db.AccessRequest.email == email))
    if existing and existing.status in ('denied', 'revoked'):
        existing.status = 'pending'
        existing.digest = None
        existing.expires = 0
        existing.created = time.time()
        s.commit()
    elif not existing:
        s.add(db.AccessRequest(email=email))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
    return {'message': 'Request recorded. The owner will review your email and contact you separately.'}


@app.get('/api/access')
def access_list(user: User, s: DB):
    owner_only(user)
    return [{'id': r.id, 'email': r.email, 'status': r.status, 'created': r.created}
            for r in s.scalars(select(db.AccessRequest).order_by(db.AccessRequest.created.desc()))]


class AccessDecision(BaseModel):
    action: str = Field(pattern='^(approve|deny|revoke)$')


@app.post('/api/access/{id}/review')
def review_access(id: str, body: AccessDecision, user: User, s: DB):
    owner_only(user)
    row = s.get(db.AccessRequest, id)
    if not row or row.email == settings.owner_email.strip().lower():
        raise HTTPException(400, 'This request cannot be changed.')
    if body.action == 'approve':
        if row.status == 'accepted':
            raise HTTPException(409, 'Revoke existing access before inviting again.')
        token = secrets.token_urlsafe(32)
        row.status = 'invited'
        row.digest = hashlib.sha256(token.encode()).hexdigest()
        row.expires = time.time() + 86400 * 2
        s.commit()
        return {'invitation': settings.origin + '/#invite=' + token}
    row.status = 'denied' if body.action == 'deny' else 'revoked'
    row.digest = None
    account = s.scalar(select(db.User).where(db.User.email == row.email))
    if account:
        for session_row in s.scalars(select(db.SessionToken).where(db.SessionToken.user_id == account.id)):
            s.delete(session_row)
    s.commit()
    return {'ok': True}


class AcceptInvite(Credentials):
    token: str = Field(min_length=32, max_length=128)


@app.post('/api/access/accept')
def accept_invite(body: AcceptInvite, request: Request, response: Response, s: DB):
    throttle(s, 'invite:' + (request.client.host if request.client else 'unknown'))
    email = body.email.strip().lower()
    result = s.execute(update(db.AccessRequest).where(
        db.AccessRequest.email == email, db.AccessRequest.status == 'invited',
        db.AccessRequest.digest == hashlib.sha256(body.token.encode()).hexdigest(),
        db.AccessRequest.expires > time.time()).values(status='accepted', digest=None))
    if result.rowcount != 1:
        s.rollback()
        raise HTTPException(400, 'Invitation is invalid, expired, or already used.')
    user = s.scalar(select(db.User).where(db.User.email == email))
    if user:
        user.password = passwords.hash(body.password)
    else:
        user = db.User(email=email, password=passwords.hash(body.password))
        s.add(user)
    s.flush()
    return issue_session(s, user, response)


@app.get('/api/health')
def health(s: DB):
    s.execute(text('SELECT 1'))
    return {'status': 'ok'}


@app.get('/api/status')
def status(user: User):
    configured = bool(settings.model and (settings.provider == 'ollama' or
        (settings.provider == 'openai' and settings.api_key)))
    try:
        adapter_capabilities = asdict(providers.provider_capabilities(settings.provider))
    except providers.ProviderError:
        adapter_capabilities = None
    return {'chat_configured': configured, 'research_configured': configured and bool(settings.search_key),
        'adapter_capabilities': adapter_capabilities, 'model_evaluation': 'not evaluated',
        'provider': settings.provider, 'model': settings.model or 'Not configured',
        'missing': ([name for name, present in [('FRIDAY_MODEL', settings.model), ('FRIDAY_SEARCH_KEY', settings.search_key)] if not present]
            + (['FRIDAY_API_KEY'] if settings.provider == 'openai' and not settings.api_key else [])),
        'capabilities': {'persistent_chat': 'implemented', 'research': 'implemented; requires configured services',
            'physics_lift_checker': 'implemented; deterministic narrow calculator, not a trained model',
            'voice': 'browser TTS available; dictation depends on browser speech recognition',
            'operating_desks': 'implemented; owner-only, record-backed templates; no send or payment',
            'memory': 'per-person operating records implemented; general AI memory planned', 'computer_use': 'planned', 'coding_sandbox': 'planned',
            'business_integrations': 'planned', 'mobile_apps': 'planned', 'device_pairing': 'planned'}}


@app.post('/api/physics/check')
def physics_check(body: physics.LiftSupportInput, user: User):
    try:
        return physics.solve_lift_support(body)
    except physics.PhysicsInputError as exc:
        raise HTTPException(422, str(exc)) from exc


class Title(BaseModel):
    title: str = Field(default='New conversation', min_length=1, max_length=120)


@app.post('/api/conversations', status_code=201)
def new_conversation(body: Title, user: User, s: DB):
    c = db.Conversation(user_id=user.id, title=body.title)
    s.add(c)
    s.commit()
    return {'id': c.id, 'title': c.title}


@app.get('/api/conversations')
def conversations(user: User, s: DB):
    rows = s.scalars(select(db.Conversation).where(db.Conversation.user_id == user.id).order_by(db.Conversation.created.desc()).limit(200))
    return [{'id': c.id, 'title': c.title} for c in rows]


@app.get('/api/conversations/{id}')
def conversation(id: str, user: User, s: DB):
    c = require_owned(s, db.Conversation, id, user)
    messages = s.scalars(select(db.Message).where(db.Message.conversation_id == id).order_by(db.Message.created, db.Message.id))
    jobs = s.scalars(select(db.Job).where(db.Job.conversation_id == id).order_by(db.Job.created.desc()).limit(10))
    return {'id': c.id, 'title': c.title, 'messages': [{'id': m.id, 'role': m.role, 'text': m.text} for m in messages], 'jobs': [job_view(j) for j in jobs]}


class Submit(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    request_key: str = Field(min_length=16, max_length=80)


def submit_job(s, user, body, kind, conversation_id=None):
    existing = s.scalar(select(db.Job).where(db.Job.user_id == user.id, db.Job.request_key == body.request_key))
    if existing:
        if existing.goal != body.text.strip() or existing.kind != kind or existing.conversation_id != conversation_id:
            raise HTTPException(409, 'Request key already belongs to a different action.')
        return job_view(existing)
    if not body.text.strip():
        raise HTTPException(422, 'Enter a request.')
    if settings.provider not in ('openai', 'ollama'):
        raise HTTPException(503, 'The selected FRIDAY_PROVIDER has no installed adapter. No AI response has been simulated.')
    if not settings.model:
        raise HTTPException(503, 'Configure FRIDAY_MODEL on the server. No AI response has been simulated.')
    if settings.provider == 'openai' and not settings.api_key:
        raise HTTPException(503, 'Configure FRIDAY_API_KEY on the server. No AI response has been simulated.')
    if kind == 'research' and not settings.search_key:
        raise HTTPException(503, 'Configure FRIDAY_SEARCH_KEY on the server for research.')
    day = int(time.time() // 86400)
    s.execute(update(db.User).where(db.User.id == user.id, db.User.quota_day != day).values(quota_day=day, quota_used=0))
    reserved = s.execute(update(db.User).where(db.User.id == user.id, db.User.quota_used < settings.daily_jobs).values(quota_used=db.User.quota_used + 1))
    if reserved.rowcount != 1:
        s.rollback()
        raise HTTPException(429, 'Daily job limit reached.')
    # User-row lock above serializes quota, active job and conversation checks.
    active = s.scalar(select(func.count()).select_from(db.Job).where(db.Job.user_id == user.id, db.Job.status.not_in(TERMINAL)))
    if active >= settings.max_active_jobs:
        s.rollback()
        raise HTTPException(429, 'Active job limit reached.')
    if conversation_id:
        busy = s.scalar(select(db.Job.id).where(db.Job.conversation_id == conversation_id, db.Job.status.not_in(TERMINAL)))
        if busy:
            s.rollback()
            raise HTTPException(409, 'Wait for this conversation’s current response or stop it.')
    j = db.Job(user_id=user.id, conversation_id=conversation_id, kind=kind, goal=body.text.strip(), request_key=body.request_key)
    s.add(j)
    if conversation_id:
        s.add(db.Message(conversation_id=conversation_id, role='user', text=body.text.strip()))
        c = s.get(db.Conversation, conversation_id)
        if c.title == 'New conversation':
            c.title = body.text.strip()[:80]
    try:
        s.flush()
        event(s, j, 'Request saved. Waiting for an available worker.')
        s.commit()
    except IntegrityError:
        s.rollback()
        existing = s.scalar(select(db.Job).where(db.Job.user_id == user.id, db.Job.request_key == body.request_key))
        if existing and existing.goal == body.text.strip() and existing.kind == kind and existing.conversation_id == conversation_id:
            return job_view(existing)
        raise HTTPException(409, 'Conflicting request key.')
    return job_view(j)


@app.post('/api/conversations/{id}/messages', status_code=202)
def send(id: str, body: Submit, user: User, s: DB):
    require_owned(s, db.Conversation, id, user)
    return submit_job(s, user, body, 'chat', id)


@app.post('/api/projects', status_code=202)
def research(body: Submit, user: User, s: DB):
    if len(body.text) > 2000:
        raise HTTPException(422, 'Research question must be 2000 characters or fewer.')
    return submit_job(s, user, body, 'research')


def job_view(j):
    return {'id': j.id, 'kind': j.kind, 'goal': j.goal, 'status': j.status, 'stage': j.stage,
        'partial': j.partial, 'error': j.error, 'attempts': j.attempts, 'created': j.created}


@app.get('/api/projects')
def projects(user: User, s: DB):
    return [job_view(j) for j in s.scalars(select(db.Job).where(db.Job.user_id == user.id, db.Job.kind == 'research').order_by(db.Job.created.desc()).limit(100))]


@app.get('/api/jobs/{id}')
def job_detail(id: str, user: User, s: DB):
    j = require_owned(s, db.Job, id, user)
    artifact = s.scalar(select(db.Artifact).where(db.Artifact.job_id == id))
    usage = s.get(db.Usage, id)
    return {**job_view(j), 'plan': j.checkpoint.get('plan', []),
        'events': [{'id': e.id, 'text': e.text, 'created': e.created} for e in s.scalars(select(db.Event).where(db.Event.job_id == id).order_by(db.Event.id))],
        'sources': [{'position': x.position, 'title': x.title, 'url': x.url, 'error': x.error, 'retrieved': x.retrieved} for x in s.scalars(select(db.Source).where(db.Source.job_id == id).order_by(db.Source.position))],
        'artifact': artifact.content if artifact else None,
        'usage': {'input_tokens': usage.input_tokens, 'output_tokens': usage.output_tokens, 'status': usage.status, 'model': usage.model} if usage else None}


@app.post('/api/jobs/{id}/cancel')
def cancel(id: str, user: User, s: DB):
    require_owned(s, db.Job, id, user)
    changed = s.execute(update(db.Job).where(db.Job.id == id, db.Job.status.not_in(TERMINAL)).values(status='cancelled', lease=None))
    if changed.rowcount:
        j = s.get(db.Job, id, populate_existing=True)
        event(s, j, 'Cancelled. No subsequent steps will start; a request already sent may still incur usage.')
        usage = s.get(db.Usage, id)
        if usage and usage.status == 'reserved':
            usage.status = 'uncertain'
    s.commit()
    return {'status': s.get(db.Job, id, populate_existing=True).status}


@app.get('/api/jobs/{id}/report')
def download(id: str, user: User, s: DB):
    require_owned(s, db.Job, id, user)
    a = s.scalar(select(db.Artifact).where(db.Artifact.job_id == id))
    if not a:
        raise HTTPException(404, 'Report is not ready.')
    return PlainTextResponse(a.content, headers={'Content-Disposition': 'attachment; filename="friday-report.md"'})


class CompanyInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=120)
    offer: str = Field(default='UNKNOWN', max_length=2000)
    audience: str = Field(default='UNKNOWN', max_length=2000)
    channel: str = Field(default='UNKNOWN', max_length=2000)
    money_rules: str = Field(default='UNKNOWN', max_length=2000)


class CompanyNotes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    offer: str = Field(max_length=2000)
    audience: str = Field(max_length=2000)
    channel: str = Field(max_length=2000)
    money_rules: str = Field(max_length=2000)


class PersonInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: Literal['creator', 'editor', 'other']
    name: str = Field(min_length=1, max_length=120)
    published_video_title: str = Field(default='', max_length=240)
    published_video_url: str = Field(default='', max_length=1000)
    video_verified: bool = False
    paid_on_time: Literal['yes', 'no', 'UNKNOWN'] = 'UNKNOWN'
    open_loop: str = Field(default='', max_length=1000)
    join_evidence: str = Field(default='', max_length=1000)
    opted_out: bool = False


class PersonNotes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    published_video_title: str | None = Field(default=None, max_length=240)
    published_video_url: str | None = Field(default=None, max_length=1000)
    video_verified: bool | None = None
    paid_on_time: Literal['yes', 'no', 'UNKNOWN'] | None = None
    open_loop: str | None = Field(default=None, max_length=1000)
    join_evidence: str | None = Field(default=None, max_length=1000)
    opted_out: bool | None = None
    record_contact_now: bool = False


class CreatorJobInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    creator_id: str
    title: str = Field(min_length=1, max_length=240)
    brief: str = Field(min_length=1, max_length=4000)
    creator_confirmation: str = Field(min_length=1, max_length=1000)
    sample_scope: str = Field(default='', max_length=1000)
    sample_fee: str = Field(default='', max_length=80)
    sample_deadline: str = Field(default='', max_length=80)
    invoice_amount: str = Field(default='', max_length=80)


class ToolInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_key: str = Field(min_length=16, max_length=80)
    person_id: str | None = None
    job_id: str | None = None


def company_view(row):
    return {field: getattr(row, field) for field in ('id', 'name', 'offer', 'audience', 'channel', 'money_rules', 'created')}


def person_view(row):
    return {field: getattr(row, field) for field in ('id', 'company_id', 'role', 'name', 'published_video_title',
        'published_video_url', 'video_verified_at', 'last_job', 'paid_on_time', 'open_loop', 'last_contact_at',
        'joined_at', 'join_evidence', 'opted_out', 'created')}


def job_operating_view(row):
    return {field: getattr(row, field) for field in ('id', 'company_id', 'creator_id', 'title', 'brief',
        'creator_confirmation', 'sample_scope', 'sample_fee', 'sample_deadline', 'invoice_amount', 'created')}


def draft_view(row):
    return {field: getattr(row, field) for field in ('id', 'company_id', 'person_id', 'job_id', 'tool',
        'request_key', 'request', 'result', 'draft', 'status', 'created')}


def operating_company(s, company_id, user):
    owner_only(user)
    row = s.get(db.OperatingCompany, company_id)
    if not row or row.user_id != user.id:
        raise HTTPException(404, 'Company desk not found.')
    return row


def operating_person(s, company_id, person_id):
    row = s.get(db.OperatingPerson, person_id) if person_id else None
    if person_id and (not row or row.company_id != company_id):
        raise HTTPException(404, 'Person record not found in this company desk.')
    return row


def operating_job(s, company_id, job_id):
    row = s.get(db.OperatingJob, job_id) if job_id else None
    if job_id and (not row or row.company_id != company_id):
        raise HTTPException(404, 'Creator job not found in this company desk.')
    return row


@app.get('/api/operating/companies')
def operating_companies(user: User, s: DB):
    owner_only(user)
    quicut = s.scalar(select(db.OperatingCompany).where(db.OperatingCompany.user_id == user.id,
        db.OperatingCompany.name == 'QuiCut'))
    if not quicut:
        s.add(db.OperatingCompany(user_id=user.id, name='QuiCut',
            offer='Match video creators with editors for a paid cut.',
            audience='Creators are required; editors follow real creator jobs.',
            channel='UNKNOWN',
            money_rules='Paid cut. Editor paid sample only after a real creator job exists. Amounts and escrow: UNKNOWN. Owner sends and pays.'))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
    return [company_view(row) for row in s.scalars(select(db.OperatingCompany).where(
        db.OperatingCompany.user_id == user.id).order_by(db.OperatingCompany.created))]


@app.post('/api/operating/companies', status_code=201)
def operating_new_company(body: CompanyInput, user: User, s: DB):
    owner_only(user)
    data = {key: operating.safe_note(value) or 'UNKNOWN' for key, value in body.model_dump().items()}
    if data['name'] == 'UNKNOWN':
        raise HTTPException(422, 'Name a real company.')
    row = db.OperatingCompany(user_id=user.id, **data)
    s.add(row)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        raise HTTPException(409, 'Company desk already exists.')
    return company_view(row)


@app.put('/api/operating/companies/{company_id}/notes')
def operating_notes(company_id: str, body: CompanyNotes, user: User, s: DB):
    row = operating_company(s, company_id, user)
    for field, value in body.model_dump().items():
        setattr(row, field, operating.safe_note(value) or 'UNKNOWN')
    s.commit()
    return company_view(row)


@app.get('/api/operating/companies/{company_id}')
def operating_desk(company_id: str, user: User, s: DB):
    row = operating_company(s, company_id, user)
    people = list(s.scalars(select(db.OperatingPerson).where(db.OperatingPerson.company_id == row.id).order_by(db.OperatingPerson.created)))
    jobs = list(s.scalars(select(db.OperatingJob).where(db.OperatingJob.company_id == row.id).order_by(db.OperatingJob.created.desc())))
    drafts = list(s.scalars(select(db.OperatingDraft).where(db.OperatingDraft.company_id == row.id).order_by(db.OperatingDraft.created.desc()).limit(100)))
    return {'company': company_view(row), 'people': [person_view(p) for p in people],
        'jobs': [job_operating_view(j) for j in jobs], 'drafts': [draft_view(d) for d in drafts]}


@app.post('/api/operating/companies/{company_id}/people', status_code=201)
def operating_new_person(company_id: str, body: PersonInput, user: User, s: DB):
    operating_company(s, company_id, user)
    data = body.model_dump()
    verified = data.pop('video_verified')
    for field in ('name', 'published_video_title', 'published_video_url', 'open_loop', 'join_evidence'):
        data[field] = operating.safe_note(data[field])
    if verified and not (data['published_video_title'] and data['published_video_url']):
        raise HTTPException(422, 'Video attestation requires a title and URL.')
    if data['join_evidence'] and data['role'] != 'creator':
        raise HTTPException(422, 'Demand-side join evidence is for creators only.')
    row = db.OperatingPerson(company_id=company_id, **data,
        video_verified_at=time.time() if verified else None,
        joined_at=time.time() if data['join_evidence'] else None)
    s.add(row)
    s.commit()
    return person_view(row)


@app.patch('/api/operating/companies/{company_id}/people/{person_id}')
def operating_update_person(company_id: str, person_id: str, body: PersonNotes, user: User, s: DB):
    operating_company(s, company_id, user)
    row = operating_person(s, company_id, person_id)
    data = body.model_dump(exclude_unset=True)
    if data.pop('record_contact_now', False):
        row.last_contact_at = time.time()
    if 'video_verified' in data:
        row.video_verified_at = time.time() if data.pop('video_verified') else None
    for field, value in data.items():
        if field in ('published_video_title', 'published_video_url', 'open_loop', 'join_evidence'):
            value = operating.safe_note(value or '')
        if field == 'join_evidence' and value and row.role != 'creator':
            raise HTTPException(422, 'Demand-side join evidence is for creators only.')
        setattr(row, field, value)
        if field == 'join_evidence':
            row.joined_at = time.time() if value and not row.joined_at else row.joined_at if value else None
    if row.video_verified_at and not (row.published_video_title and row.published_video_url):
        raise HTTPException(422, 'Video attestation requires a title and URL.')
    s.commit()
    return person_view(row)


@app.post('/api/operating/companies/{company_id}/jobs', status_code=201)
def operating_new_job(company_id: str, body: CreatorJobInput, user: User, s: DB):
    operating_company(s, company_id, user)
    creator = operating_person(s, company_id, body.creator_id)
    if not creator or creator.role != 'creator':
        raise HTTPException(422, 'A creator record is required for a real job.')
    data = body.model_dump()
    for field in ('title', 'brief', 'creator_confirmation', 'sample_scope', 'sample_fee', 'sample_deadline', 'invoice_amount'):
        data[field] = operating.safe_note(data[field])
    if not data['creator_confirmation']:
        raise HTTPException(422, 'Record how the creator confirmed this job.')
    row = db.OperatingJob(company_id=company_id, **data)
    s.add(row)
    s.flush()
    creator.last_job = row.id
    s.commit()
    return job_operating_view(row)


@app.post('/api/operating/companies/{company_id}/tools/{tool}', status_code=201)
def operating_tool(company_id: str, tool: str, body: ToolInput, user: User, s: DB):
    company = operating_company(s, company_id, user)
    if tool not in operating.TOOLS:
        raise HTTPException(404, 'Unknown draft-only tool.')
    if not settings.model or settings.provider not in ('ollama', 'openai') or (settings.provider == 'openai' and not settings.api_key):
        return {'status': 'NOT_RUN'}
    request = body.model_dump()
    existing = s.scalar(select(db.OperatingDraft).where(db.OperatingDraft.company_id == company_id,
        db.OperatingDraft.request_key == body.request_key))
    if existing:
        if existing.tool != tool or existing.request != request:
            raise HTTPException(409, 'Request key belongs to a different draft request.')
        return draft_view(existing)
    person = operating_person(s, company_id, body.person_id)
    job = operating_job(s, company_id, body.job_id)
    if job and person and person.role == 'creator' and job.creator_id != person.id:
        raise HTTPException(422, 'Creator and job records do not match.')
    try:
        output, result = operating.draft(s, company, tool, person, job)
    except operating.DraftBlocked as exc:
        raise HTTPException(409, str(exc)) from exc
    row = db.OperatingDraft(company_id=company.id, person_id=body.person_id, job_id=body.job_id,
        tool=tool, request_key=body.request_key, request=request, result={**result, 'generation': 'validated_template',
        'configured_model': settings.model, 'model_called': False}, draft=output)
    s.add(row)
    try:
        s.commit()
    except IntegrityError:
        s.rollback()
        raise HTTPException(409, 'Concurrent draft request; refresh the desk.')
    return draft_view(row)


class StudyReviewInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    reference_status: Literal['verified', 'invalid']
    reference_note: str = Field(min_length=1, max_length=2000)
    score: Literal[0, 1, 2] | None = None
    rationale: str = Field(default='', max_length=2000)


@app.get('/api/evaluation/study-pack')
def study_pack(user: User, s: DB):
    owner_only(user)
    manifest, rows = study_review.load_run()
    saved = {row.case_id: study_review.review_view(row, user.email) for row in s.scalars(
        select(db.StudyReview).where(db.StudyReview.run_id == manifest['run_id'], db.StudyReview.user_id == user.id))}
    return {'run_id': manifest['run_id'], 'model_id': manifest['model_id'],
        'execution_path': manifest.get('execution_path', 'UNKNOWN'), 'cases': [
            {**row, **saved.get(row['id'], {'reference_review': None, 'review': None})} for row in rows]}


@app.post('/api/evaluation/study-pack/{case_id}/review')
def save_study_review(case_id: str, body: StudyReviewInput, user: User, s: DB):
    owner_only(user)
    manifest, rows = study_review.load_run()
    if case_id not in {row['id'] for row in rows}:
        raise HTTPException(404, 'Study case not found.')
    reference_note = body.reference_note.strip()
    rationale = body.rationale.strip()
    if not reference_note or (body.reference_status == 'verified' and (body.score is None or not rationale)):
        raise HTTPException(422, 'A verified reference and answer score require specific review notes.')
    if body.reference_status == 'invalid' and (body.score is not None or rationale):
        raise HTTPException(422, 'An invalid reference cannot support an answer score.')
    row = s.scalar(select(db.StudyReview).where(db.StudyReview.run_id == manifest['run_id'],
        db.StudyReview.case_id == case_id, db.StudyReview.user_id == user.id))
    if not row:
        row = db.StudyReview(run_id=manifest['run_id'], case_id=case_id, user_id=user.id)
        s.add(row)
    row.reference_status = body.reference_status
    row.reference_note = reference_note
    row.score = body.score
    row.rationale = rationale
    row.reviewed_at = time.time()
    s.commit()
    return study_review.review_view(row, user.email)


@app.get('/api/evaluation/study-pack/export')
def export_study_reviews(user: User, s: DB):
    owner_only(user)
    manifest, rows = study_review.load_run()
    saved = {row.case_id: study_review.review_view(row, user.email) for row in s.scalars(
        select(db.StudyReview).where(db.StudyReview.run_id == manifest['run_id'], db.StudyReview.user_id == user.id))}
    content = ''.join(json.dumps({**row, **saved.get(row['id'],
        {'reference_review': None, 'review': None})}, ensure_ascii=False) + '\n' for row in rows)
    return PlainTextResponse(content, media_type='application/x-ndjson',
        headers={'Content-Disposition': 'attachment; filename="friday-study-human-reviews.jsonl"'})


frontend = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if frontend.exists():
    app.mount('/assets', StaticFiles(directory=frontend / 'assets'), name='assets')

    @app.get('/')
    def index():
        return FileResponse(frontend / 'index.html')
