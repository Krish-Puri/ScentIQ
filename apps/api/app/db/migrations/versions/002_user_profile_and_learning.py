"""User Profile and Feedback Learning Schema Additions.

Revision ID: 002_user_profile_and_learning
Revises: 001_initial_schema
Create Date: 2026-11-05 13:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_user_profile_and_learning'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Expand user_profiles with structured onboarding and preference attributes
    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.add_column(sa.Column('familiarity_level', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('preferred_families', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('preferred_notes', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('disliked_notes', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('preferred_accords', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('disliked_accords', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('preferred_concentrations', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('longevity_preference', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('projection_preference', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # 2. Expand user_feedbacks with updated_at timestamp and unique constraint
    with op.batch_alter_table('user_feedbacks') as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_unique_constraint('uq_user_fragrance_feedback', ['user_id', 'fragrance_id'])


def downgrade() -> None:
    with op.batch_alter_table('user_feedbacks') as batch_op:
        batch_op.drop_constraint('uq_user_fragrance_feedback', type_='unique')
        batch_op.drop_column('updated_at')

    with op.batch_alter_table('user_profiles') as batch_op:
        batch_op.drop_column('onboarding_completed')
        batch_op.drop_column('projection_preference')
        batch_op.drop_column('longevity_preference')
        batch_op.drop_column('preferred_concentrations')
        batch_op.drop_column('disliked_accords')
        batch_op.drop_column('preferred_accords')
        batch_op.drop_column('disliked_notes')
        batch_op.drop_column('preferred_notes')
        batch_op.drop_column('preferred_families')
        batch_op.drop_column('familiarity_level')
