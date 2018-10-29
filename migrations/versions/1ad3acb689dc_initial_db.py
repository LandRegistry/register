"""Initial db

Revision ID: 1ad3acb689dc
Revises: None
Create Date: 2017-01-27 14:47:09.216799

"""

# revision identifiers, used by Alembic.
revision = '1ad3acb689dc'
down_revision = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from flask import current_app


def upgrade():

    op.create_table('item',
                    sa.Column('item_hash', sa.String(), primary_key=True),
                    sa.Column('item', postgresql.JSONB(), nullable=False))

    op.create_table('entry',
                    sa.Column('entry_number', sa.Integer(), primary_key=True),
                    sa.Column('entry_timestamp', sa.DateTime(), nullable=False),
                    sa.Column('item_hash', sa.String(), sa.ForeignKey('item.item_hash')),
                    sa.Column('key', sa.String(), nullable=False, index=True),
                    sa.Column('item_signature', sa.String(), nullable=False))

    op.create_table('leaf_hashes',
                    sa.Column('entry_number', sa.Integer(), sa.ForeignKey('entry.entry_number'), index=True),
                    sa.Column('entry_hash', sa.String(), nullable=False))

    op.create_table('branch_hashes',
                    sa.Column('start_entry_number', sa.Integer(), sa.ForeignKey('entry.entry_number')),
                    sa.Column('end_entry_number', sa.Integer(), sa.ForeignKey('entry.entry_number')),
                    sa.Column('branch_hash', sa.String(), nullable=False))

    op.create_index('ix_branch_hash_start', 'branch_hashes', ['start_entry_number'])
    op.create_index('ix_branch_hash_end', 'branch_hashes', ['end_entry_number'])
    op.create_index('ix_branch_hash_start_end', 'branch_hashes', ['start_entry_number', 'end_entry_number'])
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO " + current_app.config.get('APP_SQL_USERNAME'))


def downgrade():
    op.drop_index('ix_branch_hash_start_end')
    op.drop_index('ix_branch_hash_end')
    op.drop_index('ix_branch_hash_start')
    op.drop_table('branch_hashes')
    op.drop_table('leaf_hashes')
    op.drop_table('entry')
    op.drop_table('item')
