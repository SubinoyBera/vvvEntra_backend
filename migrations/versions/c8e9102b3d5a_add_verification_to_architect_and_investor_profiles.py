"""add verification, payout and video to architect and investor profiles

Revision ID: c8e9102b3d5a
Revises: b7d8291a0c4f
Create Date: 2026-10-16 02:00:00.000000

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
    # 1. Clean up obsolete separate verification tables if present
    op.execute("DROP TABLE IF EXISTS verification_videos CASCADE;")
    op.execute("DROP TABLE IF EXISTS user_verifications CASCADE;")

    # 2. Allow nullable wizard fields on architect_profiles so verification can happen anytime
    op.alter_column('architect_profiles', 'headline', nullable=True)
    op.alter_column('architect_profiles', 'location', nullable=True)
    op.alter_column('architect_profiles', 'opportunity_description', nullable=True)
    op.alter_column('architect_profiles', 'doc_depth', nullable=True)
    op.alter_column('architect_profiles', 'submission_timeline', nullable=True)

    # 3. Add verification, payout, and video columns to architect_profiles
    op.add_column('architect_profiles', sa.Column('linkedin_url', sa.String(length=500), nullable=True))
    op.add_column('architect_profiles', sa.Column('is_linkedin_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('architect_profiles', sa.Column('linkedin_verified_at', sa.DateTime(timezone=True), nullable=True))

    op.add_column('architect_profiles', sa.Column('payout_account_id', sa.String(length=255), nullable=True))
    op.add_column('architect_profiles', sa.Column('payout_provider', sa.String(length=50), server_default='stripe', nullable=True))
    op.add_column('architect_profiles', sa.Column('payout_bank_name', sa.String(length=100), nullable=True))
    op.add_column('architect_profiles', sa.Column('payout_last4', sa.String(length=10), nullable=True))
    op.add_column('architect_profiles', sa.Column('payout_currency', sa.String(length=10), server_default='USD', nullable=True))
    op.add_column('architect_profiles', sa.Column('is_payout_connected', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('architect_profiles', sa.Column('payout_connected_at', sa.DateTime(timezone=True), nullable=True))

    op.add_column('architect_profiles', sa.Column('user_video', sa.LargeBinary(), nullable=True))
    op.add_column('architect_profiles', sa.Column('user_video_content_type', sa.String(length=50), server_default='video/webm', nullable=True))
    op.add_column('architect_profiles', sa.Column('is_video_submitted', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('architect_profiles', sa.Column('video_submitted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('architect_profiles', sa.Column('is_video_verified', sa.String(length=20), server_default='False', nullable=False))
    op.add_column('architect_profiles', sa.Column('video_verified_at', sa.DateTime(timezone=True), nullable=True))

    # 4. Allow nullable wizard fields on investor_profiles
    op.alter_column('investor_profiles', 'focus', nullable=True)
    op.alter_column('investor_profiles', 'location', nullable=True)
    op.alter_column('investor_profiles', 'looking_for', nullable=True)
    op.alter_column('investor_profiles', 'capital_range', nullable=True)
    op.alter_column('investor_profiles', 'deployment_timeline', nullable=True)

    # 5. Add linkedin verification to investor_profiles
    op.add_column('investor_profiles', sa.Column('linkedin_url', sa.String(length=500), nullable=True))
    op.add_column('investor_profiles', sa.Column('is_linkedin_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('investor_profiles', sa.Column('linkedin_verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('investor_profiles', 'linkedin_verified_at')
    op.drop_column('investor_profiles', 'is_linkedin_verified')
    op.drop_column('investor_profiles', 'linkedin_url')

    op.drop_column('architect_profiles', 'video_verified_at')
    op.drop_column('architect_profiles', 'is_video_verified')
    op.drop_column('architect_profiles', 'video_submitted_at')
    op.drop_column('architect_profiles', 'is_video_submitted')
    op.drop_column('architect_profiles', 'user_video_content_type')
    op.drop_column('architect_profiles', 'user_video')
    op.drop_column('architect_profiles', 'payout_connected_at')
    op.drop_column('architect_profiles', 'is_payout_connected')
    op.drop_column('architect_profiles', 'payout_currency')
    op.drop_column('architect_profiles', 'payout_last4')
    op.drop_column('architect_profiles', 'payout_bank_name')
    op.drop_column('architect_profiles', 'payout_provider')
    op.drop_column('architect_profiles', 'payout_account_id')
    op.drop_column('architect_profiles', 'linkedin_verified_at')
    op.drop_column('architect_profiles', 'is_linkedin_verified')
    op.drop_column('architect_profiles', 'linkedin_url')
