"""add payout and video verification columns to user_verifications

Revision ID: d9f0123c4e6b
Revises: c8e9102b3d5a
Create Date: 2026-10-15 04:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9f0123c4e6b'
down_revision: Union[str, Sequence[str], None] = 'c8e9102b3d5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_verifications', sa.Column('payout_account_id', sa.String(length=255), nullable=True))
    op.add_column('user_verifications', sa.Column('payout_provider', sa.String(length=50), server_default='stripe', nullable=True))
    op.add_column('user_verifications', sa.Column('payout_bank_name', sa.String(length=100), nullable=True))
    op.add_column('user_verifications', sa.Column('payout_last4', sa.String(length=10), nullable=True))
    op.add_column('user_verifications', sa.Column('payout_currency', sa.String(length=10), server_default='USD', nullable=True))
    op.add_column('user_verifications', sa.Column('is_payout_connected', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user_verifications', sa.Column('payout_connected_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('user_verifications', sa.Column('is_video_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('user_verifications', sa.Column('video_verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('user_verifications', 'video_verified_at')
    op.drop_column('user_verifications', 'is_video_verified')
    op.drop_column('user_verifications', 'payout_connected_at')
    op.drop_column('user_verifications', 'is_payout_connected')
    op.drop_column('user_verifications', 'payout_currency')
    op.drop_column('user_verifications', 'payout_last4')
    op.drop_column('user_verifications', 'payout_bank_name')
    op.drop_column('user_verifications', 'payout_provider')
    op.drop_column('user_verifications', 'payout_account_id')
