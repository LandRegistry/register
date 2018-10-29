import os
from urllib.parse import quote_plus

# RULES OF CONFIG:
# 1. No region specific code. Regions are defined by setting the OS environment variables appropriately to build up the
# desired behaviour.
# 2. No use of defaults when getting OS environment variables. They must all be set to the required values prior to the
# app starting.
# 3. This is the only file in the app where os.environ should be used.

# For logging
FLASK_LOG_LEVEL = os.environ['LOG_LEVEL']

# For health route
COMMIT = os.environ['COMMIT']

# This APP_NAME variable is to allow changing the app name when the app is running in a cluster. So that
# each app in the cluster will have a unique name.
APP_NAME = os.environ['APP_NAME']

# --- Database variables start
# These must all be set in the OS environment.
# The password must be the correct one for either the app user or alembic user,
# depending on which will be used (which is controlled by the SQL_USE_ALEMBIC_USER variable)
SQL_HOST = os.environ['SQL_HOST']
SQL_DATABASE = os.environ['SQL_DATABASE']
SQL_PASSWORD = os.environ['SQL_PASSWORD']
APP_SQL_USERNAME = os.environ['APP_SQL_USERNAME']
ALEMBIC_SQL_USERNAME = os.environ['ALEMBIC_SQL_USERNAME']
if os.environ['SQL_USE_ALEMBIC_USER'] == 'yes':
    FINAL_SQL_USERNAME = ALEMBIC_SQL_USERNAME
else:
    FINAL_SQL_USERNAME = APP_SQL_USERNAME
SQLALCHEMY_DATABASE_URI = 'postgres://{0}:{1}@{2}/{3}'.format(FINAL_SQL_USERNAME, quote_plus(SQL_PASSWORD), SQL_HOST,
                                                              SQL_DATABASE)
SQLALCHEMY_DATABASE_URI_ALEMBIC = 'postgres://{0}:{1}@{2}/{3}'.format(
    FINAL_SQL_USERNAME, SQL_PASSWORD, SQL_HOST, SQL_DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False  # Explicitly set this in order to remove warning on run
SQLALCHEMY_POOL_SIZE = int(os.environ['SQLALCHEMY_POOL_SIZE'])
SQLALCHEMY_POOL_RECYCLE = int(os.environ['SQLALCHEMY_POOL_RECYCLE'])
# --- Database variables end

# Rabbitmq
EXCHANGE_NAME = os.environ['EXCHANGE_NAME']
EXCHANGE_TYPE = os.environ['EXCHANGE_TYPE']
RABBIT_URL = os.environ['RABBIT_URL']

REGISTER_NAME = os.environ['REGISTER_NAME']
REGISTER_KEY_FIELD = os.environ['REGISTER_KEY_FIELD']
REGISTER_RECORD = os.environ['REGISTER_RECORD']
REGISTER_ROUTEKEY = os.environ['REGISTER_ROUTEKEY']

PUBLIC_KEY = os.environ['PUBLIC_KEY']
PUBLIC_PASSPHRASE = os.environ['PUBLIC_PASSPHRASE']

VALIDATION_BASE_URI = os.getenv('VALIDATION_BASE_URI', None)
VALIDATION_ENDPOINT = os.getenv('VALIDATION_ENDPOINT', '')

MAX_HEALTH_CASCADE = os.environ['MAX_HEALTH_CASCADE']
DEPENDENCIES = {
    "postgres": SQLALCHEMY_DATABASE_URI,
}

if VALIDATION_BASE_URI is not None:
    DEPENDENCIES['validation-api'] = VALIDATION_BASE_URI

LOGCONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            '()': 'register.extensions.JsonFormatter'
        },
        'audit': {
            '()': 'register.extensions.JsonAuditFormatter'
        }
    },
    'filters': {
        'contextual': {
            '()': 'register.extensions.ContextualFilter'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['contextual'],
            'stream': 'ext://sys.stdout'
        },
        'audit_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'audit',
            'filters': ['contextual'],
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'register': {
            'handlers': ['console'],
            'level': FLASK_LOG_LEVEL
        },
        'audit': {
            'handlers': ['audit_console'],
            'level': 'INFO'
        }
    }
}
