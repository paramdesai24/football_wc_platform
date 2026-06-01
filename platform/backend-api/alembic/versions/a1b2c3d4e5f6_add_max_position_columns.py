"""add max position columns to leagues

Revision ID: a1b2c3d4e5f6
Revises: 288e375e2a3e
Create Date: 2026-06-01 17:25:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '288e375e2a3e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'leagues' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('leagues')]

        if 'max_gk' not in existing_columns:
            op.add_column('leagues', sa.Column('max_gk', sa.Integer(), server_default='3'))
        if 'max_def' not in existing_columns:
            op.add_column('leagues', sa.Column('max_def', sa.Integer(), server_default='6'))
        if 'max_mid' not in existing_columns:
            op.add_column('leagues', sa.Column('max_mid', sa.Integer(), server_default='6'))
        if 'max_fwd' not in existing_columns:
            op.add_column('leagues', sa.Column('max_fwd', sa.Integer(), server_default='5'))

        # Update squad_size default from 15 to 20
        op.alter_column('leagues', 'squad_size', server_default='20')

        # Backfill existing rows that have NULL max values
        op.execute("UPDATE leagues SET max_gk = 3 WHERE max_gk IS NULL")
        op.execute("UPDATE leagues SET max_def = 6 WHERE max_def IS NULL")
        op.execute("UPDATE leagues SET max_mid = 6 WHERE max_mid IS NULL")
        op.execute("UPDATE leagues SET max_fwd = 5 WHERE max_fwd IS NULL")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'leagues' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('leagues')]

        if 'max_gk' in existing_columns:
            op.drop_column('leagues', 'max_gk')
        if 'max_def' in existing_columns:
            op.drop_column('leagues', 'max_def')
        if 'max_mid' in existing_columns:
            op.drop_column('leagues', 'max_mid')
        if 'max_fwd' in existing_columns:
            op.drop_column('leagues', 'max_fwd')

        op.alter_column('leagues', 'squad_size', server_default='15')
