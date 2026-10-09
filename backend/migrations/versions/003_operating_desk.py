"""Private company desks, per-person memory, creator jobs and draft audit log."""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'


def upgrade():
    op.create_table('operating_companies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('offer', sa.Text(), nullable=False),
        sa.Column('audience', sa.Text(), nullable=False),
        sa.Column('channel', sa.Text(), nullable=False),
        sa.Column('money_rules', sa.Text(), nullable=False),
        sa.Column('created', sa.Float(), nullable=False),
        sa.UniqueConstraint('user_id', 'name'))
    op.create_index('ix_operating_companies_user_id', 'operating_companies', ['user_id'])
    op.create_table('operating_people',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('operating_companies.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('published_video_title', sa.String(240), nullable=False),
        sa.Column('published_video_url', sa.Text(), nullable=False),
        sa.Column('video_verified_at', sa.Float(), nullable=True),
        sa.Column('last_job', sa.String(36), nullable=False),
        sa.Column('paid_on_time', sa.String(20), nullable=False),
        sa.Column('open_loop', sa.Text(), nullable=False),
        sa.Column('last_contact_at', sa.Float(), nullable=True),
        sa.Column('joined_at', sa.Float(), nullable=True),
        sa.Column('join_evidence', sa.Text(), nullable=False),
        sa.Column('opted_out', sa.Boolean(), nullable=False),
        sa.Column('created', sa.Float(), nullable=False))
    op.create_index('ix_operating_people_company_id', 'operating_people', ['company_id'])
    op.create_table('operating_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('operating_companies.id'), nullable=False),
        sa.Column('creator_id', sa.String(36), sa.ForeignKey('operating_people.id'), nullable=False),
        sa.Column('title', sa.String(240), nullable=False),
        sa.Column('brief', sa.Text(), nullable=False),
        sa.Column('creator_confirmation', sa.Text(), nullable=False),
        sa.Column('sample_scope', sa.Text(), nullable=False),
        sa.Column('sample_fee', sa.String(80), nullable=False),
        sa.Column('sample_deadline', sa.String(80), nullable=False),
        sa.Column('invoice_amount', sa.String(80), nullable=False),
        sa.Column('created', sa.Float(), nullable=False))
    op.create_index('ix_operating_jobs_company_id', 'operating_jobs', ['company_id'])
    op.create_table('operating_drafts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('operating_companies.id'), nullable=False),
        sa.Column('person_id', sa.String(36), sa.ForeignKey('operating_people.id'), nullable=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('operating_jobs.id'), nullable=True),
        sa.Column('tool', sa.String(40), nullable=False),
        sa.Column('request_key', sa.String(80), nullable=False),
        sa.Column('request', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('draft', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('created', sa.Float(), nullable=False),
        sa.UniqueConstraint('company_id', 'request_key'))
    op.create_index('ix_operating_drafts_company_id', 'operating_drafts', ['company_id'])


def downgrade():
    op.drop_index('ix_operating_drafts_company_id', table_name='operating_drafts')
    op.drop_table('operating_drafts')
    op.drop_index('ix_operating_jobs_company_id', table_name='operating_jobs')
    op.drop_table('operating_jobs')
    op.drop_index('ix_operating_people_company_id', table_name='operating_people')
    op.drop_table('operating_people')
    op.drop_index('ix_operating_companies_user_id', table_name='operating_companies')
    op.drop_table('operating_companies')
