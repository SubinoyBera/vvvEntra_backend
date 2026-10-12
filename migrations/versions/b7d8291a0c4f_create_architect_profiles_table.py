"""create architect_profiles table

Revision ID: b7d8291a0c4f
Revises: 423f148f12a1
Create Date: 2026-10-11 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7d8291a0c4f'
down_revision: Union[str, Sequence[str], None] = '423f148f12a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'architect_profiles',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('headline', sa.String(length=120), nullable=False),
        sa.Column('location', sa.String(length=120), nullable=False),
        sa.Column('sectors', postgresql.ARRAY(sa.String(length=40)), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('opportunity_description', sa.Text(), nullable=False),
        sa.Column(
            'doc_depth',
            sa.Enum(
                '90_120_pages',
                '120_150_pages',
                '150_plus_pages',
                'still_planning',
                name='architect_doc_depth',
                native_enum=False,
                length=30
            ),
            nullable=False
        ),
        sa.Column(
            'submission_timeline',
            sa.Enum(
                'within_30_days',
                'within_3_months',
                'later_this_year',
                'exploring',
                name='architect_submission_timeline',
                native_enum=False,
                length=30
            ),
            nullable=False
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            "doc_depth IN ('90_120_pages', '120_150_pages', '150_plus_pages', 'still_planning')",
            name=op.f('ck_architect_profiles_doc_depth_valid')
        ),
        sa.CheckConstraint(
            "submission_timeline IN ('within_30_days', 'within_3_months', 'later_this_year', 'exploring')",
            name=op.f('ck_architect_profiles_submission_timeline_valid')
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name=op.f('fk_architect_profiles_user_id_users'),
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('user_id', name=op.f('pk_architect_profiles'))
    )


def downgrade() -> None:
    op.drop_table('architect_profiles')
