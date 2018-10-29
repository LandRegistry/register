from flask_script import Manager
from register.main import app
import os
# ***** For Alembic start ******
from flask_migrate import Migrate, MigrateCommand
from register.extensions import db

migrate = Migrate(app, db)
# ***** For Alembic end ******

manager = Manager(app)

# ***** For Alembic start ******
manager.add_command('db', MigrateCommand)


@manager.command
def runserver(port=10000):
    """Run the app using flask server"""

    os.environ["PYTHONUNBUFFERED"] = "yes"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["COMMIT"] = "LOCAL"

    app.run(debug=True, port=int(port))


if __name__ == "__main__":
    manager.run()
