"""create user_verifications table

Revision ID: c8e9102b3d5a
Revises: b7d8291a0c4f
Create Date: 2026-10-14 22:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8e9102b3d5a'
down_revision: Union[str, Sequence[str], None] = 'b7d8291a0c4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_verifications',
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('account_created', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('linkedin_sub', sa.String(length=255), nullable=True),
        sa.Column('linkedin_name', sa.String(length=200), nullable=True),
        sa.Column('linkedin_headline', sa.String(length=255), nullable=True),
        sa.Column('linkedin_picture_url', sa.String(length=1000), nullable=True),
        sa.Column('linkedin_email', sa.String(length=320), nullable=True),
        sa.Column('is_linkedin_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('linkedin_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_fully_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_verifications_user_id_users'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', name=op.f('pk_user_verifications')),
        sa.UniqueConstraint('linkedin_sub', name=op.f('uq_user_verifications_linkedin_sub'))
    )


def downgrade() -> None:
    op.drop_table('user_verifications')
