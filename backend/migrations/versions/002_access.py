"""Private workspace access requests and single-use invitations."""
from alembic import op
import sqlalchemy as sa
revision = '002'
down_revision = '001'

def upgrade():
    op.create_table('access_requests',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(254), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('digest', sa.String(64), nullable=True),
        sa.Column('expires', sa.Float(), nullable=False),
        sa.Column('created', sa.Float(), nullable=False))

def downgrade():
    op.drop_table('access_requests')
