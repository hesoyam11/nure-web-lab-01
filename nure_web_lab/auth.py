import functools

from flask import (
    Blueprint, flash, g, redirect, request, session, url_for,
    render_template)
from werkzeug.security import generate_password_hash, check_password_hash

import nure_web_lab.db as db

bp = Blueprint(
    # the name of the blueprint
    'auth',
    # to make the blueprint know where it's defined
    __name__,
    # will be prepended to all the blueprint's URLs
    url_prefix='/auth'
)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        cursor = db.get_db_connection().cursor()
        cursor.execute(
            'SELECT * FROM "user" WHERE id = %s', (user_id,)
        )
        g.user = cursor.fetchone()
        cursor.close()


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']

        connection = db.get_db_connection()
        cursor = connection.cursor()
        error = None

        if not username:
            error = 'Username is required.'
        elif len(username) > db.USER_USERNAME_MAX_LENGTH:
            error = 'Username is too long.'
        elif not password:
            error = 'Password is required.'
        elif not full_name:
            error = 'Full name is required.'
        elif len(full_name) > db.USER_FULL_NAME_MAX_LENGTH:
            error = 'Full name is too long.'
        else:
            cursor.execute(
                'SELECT id FROM "user" WHERE username = %s', (username,)
            )
            if cursor.fetchone() is not None:
                error = f'User {username} is already registered.'

        if error is None:
            cursor.execute(
                'INSERT INTO "user" (username, full_name, password) VALUES (%s, %s, %s)',
                (username, full_name, generate_password_hash(password))
            )
            # Since the query above modifies data,
            # this needs to be called afterwards to save the changes.
            connection.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = db.get_db_connection().cursor()
        error = None

        cursor.execute(
            'SELECT * FROM "user" WHERE username = %s', (username,)
        )
        user = cursor.fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('auth.register'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
