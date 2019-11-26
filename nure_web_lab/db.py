"""
As far as I understand, `g` and `current_app` can be used
only inside a request handling code.
So, `get_db` and `close_db` can be called only inside
a request handling code.
"""

import click
from flask import (
    # A Flask app object is created by `flask run` script
    # that uses `create_app` app factory function.
    # So, this is the only way to access the app object
    # while handling a request.
    current_app,
    Flask,
    # A special object that is unique for each request.
    # It is used to store data that might be accessed by
    # multiple functions during the request.
    g,
)
from flask.cli import with_appcontext
import psycopg2
import psycopg2.extras


USER_USERNAME_MAX_LENGTH = 150
USER_PASSWORD_MAX_LENGTH = 128
USER_FULL_NAME_MAX_LENGTH = 180

GROUP_NAME_MAX_LENGTH = 150


def get_db_connection():
    if 'db_connection' not in g:
        g.db_connection = psycopg2.connect(
            dbname=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            host=current_app.config['DB_HOST'],
            port=current_app.config['DB_PORT'],
            cursor_factory=psycopg2.extras.DictCursor
        )
    return g.db_connection


def close_db(_e=None):
    db_connection = g.pop('db_connection', None)

    if db_connection is not None:
        db_connection.close()


def init_db():
    connection = get_db_connection()

    # `open_resource` opens a file relative to the `nure_web_lab` package.
    with current_app.open_resource('schema.sql') as f:
        cursor = connection.cursor()
        cursor.execute(f.read().decode('utf8'))
        connection.commit()
        cursor.close()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app: Flask):
    # Tell Flask to call this when cleaning up after returning a response.
    app.teardown_appcontext(close_db)
    # Now this can be called with the `flask init-db` command.
    app.cli.add_command(init_db_command)
