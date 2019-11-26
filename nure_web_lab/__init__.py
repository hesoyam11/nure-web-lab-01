import os

from flask import Flask


def create_app(test_config=None):
    """
    This application factory function creates and configures the app.
    `flask run` script automatically detects and calls this function.
    """
    app = Flask(
        __name__,
        # This tells the app that configuration files are relative
        # to the `instance` folder that is located outside the `nure_web_lab` package
        # and can hold local data that shouldn't be committed to version control,
        # such as configuration secrets and the database file.
        instance_relative_config=True
    )

    app.config.from_mapping(
        SECRET_KEY="dev",
        DB_NAME="nure_web_lab",
        DB_USER="nure_web_lab_admin",
        DB_PASSWORD="nure_web_lab_admin",
        DB_HOST="localhost",
        DB_PORT=5432
    )

    if test_config is None:
        # Load a config from the `instance_path` if exists, when not testing.
        # `config.py` can be legally used in production!
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in.
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    # Generally, a `Blueprint` is a way to organize
    # a group of related views and other code.
    from . import auth
    app.register_blueprint(auth.bp)

    return app
