"""Explicit user-controlled conversational memory."""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'


def upgrade():
    op.create_table('memories',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('label', sa.String(80), nullable=False),
        sa.Column('content', sa.String(500), nullable=False),
        sa.Column('origin', sa.String(30), nullable=False),
        sa.Column('created', sa.Float(), nullable=False),
        sa.Column('updated', sa.Float(), nullable=False))
    op.create_index('ix_memories_user_id', 'memories', ['user_id'])


def downgrade():
    op.drop_index('ix_memories_user_id', table_name='memories')
    op.drop_table('memories')

