from flask import (
    abort, Blueprint, flash, redirect, render_template, request, url_for
)
from werkzeug.security import generate_password_hash

from . import db
from auth import admin_required, login_required

bp = Blueprint('user_list', __name__, url_prefix='/users')


@bp.route('/')
@login_required
def get_user_list():
    group_id_arg = request.args.get('group_id')
    group_id = None
    group = None

    if group_id_arg is not None:
        try:
            group_id = int(group_id_arg)
        except ValueError:
            abort(400)

    cursor = db.get_db_connection().cursor()

    if group_id_arg is None:
        cursor.execute(
            'SELECT id, username, full_name, is_admin, joined_at'
            ' FROM "user" ORDER BY joined_at DESC'
        )
    else:
        cursor.execute(
            'SELECT id, name FROM "group" WHERE id = %s', (group_id,)
        )

        group = cursor.fetchone()
        if group is None:
            abort(404)

        cursor.execute(
            'SELECT u.id, u.username, u.full_name, u.is_admin, u.joined_at'
            ' FROM group_user gu INNER JOIN "user" u'
            ' ON gu.group_id = %s AND gu.user_id = u.id'
            ' ORDER BY joined_at DESC', (group_id,)
        )

    users = cursor.fetchall()
    return render_template('user_list/user_list.html', users=users, group=group)


@bp.route('/create', methods=('GET', 'POST'))
@admin_required
def create_user_item():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        is_admin = bool(request.form.get('is_admin'))

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
                error = f'User {username} is already created.'

        if error is None:
            cursor.execute(
                'INSERT INTO "user"'
                ' (username, full_name, password, is_admin)'
                ' VALUES (%s, %s, %s, %s) RETURNING id',
                (username, full_name,
                 generate_password_hash(password), is_admin)
            )
            user = cursor.fetchone()

            connection.commit()
            return redirect(url_for(
                'user_list.get_user_item', user_id=user['id']
            ))

        flash(error)

    return render_template('user_list/user_create.html')


def get_user_or_404(user_id: int, cursor):
    cursor.execute(
        'SELECT id, username, full_name, is_admin, joined_at'
        ' FROM "user" WHERE id = %s', (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        abort(404)

    return user


@bp.route('/<int:user_id>')
@login_required
def get_user_item(user_id: int):
    cursor = db.get_db_connection().cursor()
    user = get_user_or_404(user_id, cursor)

    cursor.execute(
        'SELECT g.id, g.name FROM group_user gu INNER JOIN "group" g'
        ' ON gu.user_id = %s AND gu.group_id = g.id',
        (user_id,)
    )
    user_groups = cursor.fetchall()

    return render_template(
        'user_list/user_item.html',
        user=user, user_groups=user_groups
    )


@bp.route('/<int:user_id>/edit', methods=('GET', 'POST'))
@admin_required
def edit_user_item(user_id: int):
    cursor = db.get_db_connection().cursor()
    user = get_user_or_404(user_id, cursor)

    if request.method == 'POST':
        return "WIP"

    cursor.execute(
        'SELECT g.id, g.name FROM group_user gu INNER JOIN "group" g'
        ' ON gu.user_id = %s AND gu.group_id = g.id',
        (user_id,)
    )
    user_groups = cursor.fetchall()
    user_group_ids = [user_group['id'] for user_group in user_groups]

    cursor.execute(
        'SELECT id, name FROM "group"'
    )
    groups = cursor.fetchall()

    return render_template(
        'user_list/user_edit.html',
        user=user, user_group_ids=user_group_ids, groups=groups
    )


@bp.route('/<int:user_id>/delete', methods=('POST',))
@admin_required
def delete_user_item(user_id: int):
    connection = db.get_db_connection()
    cursor = connection.cursor()
    user = get_user_or_404(user_id, cursor)

    cursor.execute('DELETE FROM "user" WHERE id = %s', (user['id'],))
    connection.commit()

    return redirect(url_for('index'))
