"""Limit user permissions

Revision ID: 2771629f25c0
Revises: 06ce82a384b0
Create Date: 2017-09-20 11:26:51.696713

"""

# revision identifiers, used by Alembic.
revision = '2771629f25c0'
down_revision = '06ce82a384b0'

from alembic import op
import sqlalchemy as sa
from flask import current_app

def upgrade():
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT SELECT, INSERT ON item, entry, leaf_hashes TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT SELECT, INSERT, DELETE ON branch_hashes TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT SELECT, UPDATE ON entry_entry_number_seq TO " + current_app.config.get('APP_SQL_USERNAME'))


def downgrade():
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO " + current_app.config.get('APP_SQL_USERNAME'))
    op.execute("GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO " + current_app.config.get('APP_SQL_USERNAME'))
