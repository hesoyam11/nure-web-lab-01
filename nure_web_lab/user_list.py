from flask import (
    abort, Blueprint, flash, redirect, render_template, request, url_for
)
from psycopg2.extras import execute_values
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
    connection = db.get_db_connection()
    cursor = connection.cursor()

    user = get_user_or_404(user_id, cursor)

    # Select all groups from the database.
    cursor.execute(
        'SELECT id, name FROM "group"'
    )
    groups = cursor.fetchall()
    group_ids = [group['id'] for group in groups]

    # Select groups of a user to which he already belongs.
    cursor.execute(
        'SELECT g.id, g.name FROM group_user gu INNER JOIN "group" g'
        ' ON gu.user_id = %s AND gu.group_id = g.id',
        (user_id,)
    )
    old_user_groups = cursor.fetchall()
    old_user_group_ids = [user_group['id'] for user_group in old_user_groups]

    if request.method == 'POST':
        full_name = request.form.get('full_name')
        is_admin = bool(request.form.get('is_admin'))
        new_user_group_ids = request.form.getlist('user_groups')

        are_new_group_ids_valid = True
        for new_user_group_id in new_user_group_ids:
            try:
                new_user_group_id = int(new_user_group_id)
            except ValueError:
                are_new_group_ids_valid = False
                break
            if new_user_group_id not in group_ids:
                are_new_group_ids_valid = False
                break

        error = None

        if not full_name:
            error = 'Full name is required.'
        elif len(full_name) > db.USER_FULL_NAME_MAX_LENGTH:
            error = 'Full name is too long.'
        elif not are_new_group_ids_valid:
            error = 'Provided new groups are invalid.'

        if error is None:
            cursor.execute(
                'UPDATE "user" SET (full_name, is_admin) = (%s, %s)'
                ' WHERE id = %s', (full_name, is_admin, user_id)
            )
            cursor.execute(
                'DELETE FROM group_user WHERE user_id = %s', (user_id,)
            )
            # A function from `psycopg2.extras` to insert many rows at once.
            execute_values(
                cursor, 'INSERT INTO group_user (user_id, group_id) VALUES %s',
                [(user_id, group_id) for group_id in new_user_group_ids]
            )
            connection.commit()
            return redirect(url_for('user_list.get_user_item', user_id=user_id))

        flash(error)

    return render_template(
        'user_list/user_edit.html',
        user=user, user_group_ids=old_user_group_ids, groups=groups
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
