"""add_auction_tables

Revision ID: 288e375e2a3e
Revises: 
Create Date: 2026-05-27 16:26:57.982101
"""
from alembic import op

from app.models.auction_models import AuctionBase


# revision identifiers, used by Alembic.
revision = '288e375e2a3e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    AuctionBase.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    AuctionBase.metadata.drop_all(bind=bind, checkfirst=True)
