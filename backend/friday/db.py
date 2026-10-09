import time
import uuid
from sqlalchemy import create_engine, event, String, Text, Float, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings


def uid():
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(Text)
    quota_day: Mapped[int] = mapped_column(Integer, default=0)
    quota_used: Mapped[int] = mapped_column(Integer, default=0)


class SessionToken(Base):
    __tablename__ = 'sessions'
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    expires: Mapped[float] = mapped_column(Float)


class AccessRequest(Base):
    __tablename__ = 'access_requests'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expires: Mapped[float] = mapped_column(Float, default=0)
    created: Mapped[float] = mapped_column(Float, default=time.time)


class AuthAttempt(Base):
    __tablename__ = 'auth_attempts'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    window: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer, default=0)


class Conversation(Base):
    __tablename__ = 'conversations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(120), default='New conversation')
    created: Mapped[float] = mapped_column(Float, default=time.time)


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    conversation_id: Mapped[str] = mapped_column(ForeignKey('conversations.id'), index=True)
    role: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)


class Job(Base):
    __tablename__ = 'jobs'
    __table_args__ = (UniqueConstraint('user_id', 'request_key'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey('conversations.id'), nullable=True)
    request_key: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(20))
    goal: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='queued', index=True)
    stage: Mapped[str] = mapped_column(String(30), default='plan')
    checkpoint: Mapped[dict] = mapped_column(JSON, default=dict)
    partial: Mapped[str] = mapped_column(Text, default='')
    error: Mapped[str] = mapped_column(Text, default='')
    lease: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lease_until: Mapped[float] = mapped_column(Float, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available: Mapped[float] = mapped_column(Float, default=0)
    created: Mapped[float] = mapped_column(Float, default=time.time)


class Source(Base):
    __tablename__ = 'sources'
    __table_args__ = (UniqueConstraint('job_id', 'position'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), index=True)
    position: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text, default='')
    error: Mapped[str] = mapped_column(Text, default='')
    retrieved: Mapped[float] = mapped_column(Float, default=time.time)


class Artifact(Base):
    __tablename__ = 'artifacts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), unique=True)
    content: Mapped[str] = mapped_column(Text)


class Event(Base):
    __tablename__ = 'events'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), index=True)
    text: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float, default=time.time)


class Usage(Base):
    __tablename__ = 'usage'
    job_id: Mapped[str] = mapped_column(ForeignKey('jobs.id'), primary_key=True)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(120))
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default='reserved')


class OperatingCompany(Base):
    __tablename__ = 'operating_companies'
    __table_args__ = (UniqueConstraint('user_id', 'name'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    offer: Mapped[str] = mapped_column(Text, default='UNKNOWN')
    audience: Mapped[str] = mapped_column(Text, default='UNKNOWN')
    channel: Mapped[str] = mapped_column(Text, default='UNKNOWN')
    money_rules: Mapped[str] = mapped_column(Text, default='UNKNOWN')
    created: Mapped[float] = mapped_column(Float, default=time.time)


class OperatingPerson(Base):
    __tablename__ = 'operating_people'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey('operating_companies.id'), index=True)
    role: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(120))
    published_video_title: Mapped[str] = mapped_column(String(240), default='')
    published_video_url: Mapped[str] = mapped_column(Text, default='')
    video_verified_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_job: Mapped[str] = mapped_column(String(36), default='')
    paid_on_time: Mapped[str] = mapped_column(String(20), default='UNKNOWN')
    open_loop: Mapped[str] = mapped_column(Text, default='')
    last_contact_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    joined_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    join_evidence: Mapped[str] = mapped_column(Text, default='')
    opted_out: Mapped[bool] = mapped_column(default=False)
    created: Mapped[float] = mapped_column(Float, default=time.time)


class OperatingJob(Base):
    __tablename__ = 'operating_jobs'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey('operating_companies.id'), index=True)
    creator_id: Mapped[str] = mapped_column(ForeignKey('operating_people.id'))
    title: Mapped[str] = mapped_column(String(240))
    brief: Mapped[str] = mapped_column(Text)
    creator_confirmation: Mapped[str] = mapped_column(Text, default='')
    sample_scope: Mapped[str] = mapped_column(Text, default='')
    sample_fee: Mapped[str] = mapped_column(String(80), default='')
    sample_deadline: Mapped[str] = mapped_column(String(80), default='')
    invoice_amount: Mapped[str] = mapped_column(String(80), default='')
    created: Mapped[float] = mapped_column(Float, default=time.time)


class OperatingDraft(Base):
    __tablename__ = 'operating_drafts'
    __table_args__ = (UniqueConstraint('company_id', 'request_key'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    company_id: Mapped[str] = mapped_column(ForeignKey('operating_companies.id'), index=True)
    person_id: Mapped[str | None] = mapped_column(ForeignKey('operating_people.id'), nullable=True)
    job_id: Mapped[str | None] = mapped_column(ForeignKey('operating_jobs.id'), nullable=True)
    tool: Mapped[str] = mapped_column(String(40))
    request_key: Mapped[str] = mapped_column(String(80))
    request: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)
    draft: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default='pending_owner_review')
    created: Mapped[float] = mapped_column(Float, default=time.time)


class StudyReview(Base):
    __tablename__ = 'study_reviews'
    __table_args__ = (UniqueConstraint('run_id', 'case_id', 'user_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(String(120), index=True)
    case_id: Mapped[str] = mapped_column(String(20))
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    reference_status: Mapped[str] = mapped_column(String(20))
    reference_note: Mapped[str] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, default='')
    reviewed_at: Mapped[float] = mapped_column(Float, default=time.time)


def make_engine(url):
    engine = create_engine(url, pool_pre_ping=True, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite') else {})
    if url.startswith('sqlite'):
        @event.listens_for(engine, 'connect')
        def pragmas(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
    return engine


engine = make_engine(settings.database_url)
Session = sessionmaker(engine, expire_on_commit=False)
