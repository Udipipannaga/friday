"""Owner-only human checks of study-pack references and model responses."""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'


def upgrade():
    op.create_table('study_reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('run_id', sa.String(120), nullable=False),
        sa.Column('case_id', sa.String(20), nullable=False),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reference_status', sa.String(20), nullable=False),
        sa.Column('reference_note', sa.Text(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('reviewed_at', sa.Float(), nullable=False),
        sa.UniqueConstraint('run_id', 'case_id', 'user_id'))
    op.create_index('ix_study_reviews_run_id', 'study_reviews', ['run_id'])
    op.create_index('ix_study_reviews_user_id', 'study_reviews', ['user_id'])


def downgrade():
    op.drop_index('ix_study_reviews_user_id', table_name='study_reviews')
    op.drop_index('ix_study_reviews_run_id', table_name='study_reviews')
    op.drop_table('study_reviews')
