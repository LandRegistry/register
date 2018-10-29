from psycopg2 import extras
from register.extensions import db
from register.app import app


def start():
    app.logger.info("Connecting to ORM")
    conn = db.engine.raw_connection()
    csr = conn.cursor(cursor_factory=extras.DictCursor)
    csr.fairy = conn
    return csr


def commit(cursor):
    app.logger.info('Commit transaction')
    cursor.fairy.commit()
    cursor.close()
    cursor.fairy.close()


def rollback(cursor):
    app.logger.warning('Rollback transaction')
    cursor.fairy.rollback()
    cursor.close()
    cursor.fairy.close()
