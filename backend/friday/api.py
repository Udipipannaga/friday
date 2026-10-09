import hashlib
import secrets
import time
from dataclasses import asdict
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import select, update, func, text
from sqlalchemy.exc import IntegrityError
from . import db, providers
from .config import settings
from .execution import TERMINAL, event

app = FastAPI(title='FRIDAY', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=[settings.origin], allow_credentials=True,
    allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'X-Friday-Request'])
passwords = PasswordHash.recommended()
dummy_hash = passwords.hash(secrets.token_urlsafe(24))


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
            'voice': 'browser TTS available; dictation depends on browser speech recognition', 'memory': 'planned', 'computer_use': 'planned', 'coding_sandbox': 'planned',
            'business_integrations': 'planned', 'mobile_apps': 'planned', 'device_pairing': 'planned'}}


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


frontend = Path(__file__).resolve().parents[2] / 'frontend' / 'dist'
if frontend.exists():
    app.mount('/assets', StaticFiles(directory=frontend / 'assets'), name='assets')

    @app.get('/')
    def index():
        return FileResponse(frontend / 'index.html')

