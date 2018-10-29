"""empty message

Revision ID: 3a298d774d3f
Revises: 1ad3acb689dc
Create Date: 2017-05-31 11:57:47.828616

"""

# revision identifiers, used by Alembic.
revision = '3a298d774d3f'
down_revision = '1ad3acb689dc'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_constraint('branch_hashes_end_entry_number_fkey', 'branch_hashes')
    op.drop_constraint('branch_hashes_start_entry_number_fkey', 'branch_hashes')


def downgrade():
    op.create_foreign_key('branch_hashes_end_entry_number_fkey',
                          'branch_hashes',
                          'entry',
                          ['end_entry_number'],
                          ['entry_number'])
    op.create_foreign_key('branch_hashes_start_entry_number_fkey',
                          'branch_hashes',
                          'entry',
                          ['start_entry_number'],
                          ['entry_number'])
