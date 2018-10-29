"""Add additional indexing

Revision ID: 06ce82a384b0
Revises: 3a298d774d3f
Create Date: 2017-06-13 14:24:17.794833

"""

# revision identifiers, used by Alembic.
revision = '06ce82a384b0'
down_revision = '3a298d774d3f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_index('ix_item_item', 'item', [sa.text('item jsonb_path_ops')], postgresql_using='gin')
    op.create_index('ix_item_item_end-date', 'item', [sa.text("(item ->> 'end-date')")], postgresql_using='btree')


def downgrade():
    op.drop_index('ix_item_item')
    op.drop_index('ix_item_item_end-date')
