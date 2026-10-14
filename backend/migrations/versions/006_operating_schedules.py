"""Owner-enabled recurring draft-only operating notes."""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'


def upgrade():
    op.create_table('operating_schedules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('company_id', sa.String(36), sa.ForeignKey('operating_companies.id'), nullable=False),
        sa.Column('tool', sa.String(40), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('next_run', sa.Float(), nullable=False),
        sa.Column('last_run', sa.Float(), nullable=True),
        sa.Column('created', sa.Float(), nullable=False),
        sa.UniqueConstraint('company_id', 'tool'))
    op.create_index('ix_operating_schedules_company_id', 'operating_schedules', ['company_id'])


def downgrade():
    op.drop_index('ix_operating_schedules_company_id', table_name='operating_schedules')
    op.drop_table('operating_schedules')

