from flask import (
    abort, Blueprint, render_template, request
)

from . import db
from auth import login_required

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


@bp.route('/<int:user_id>')
@login_required
def get_user_item(user_id: int):
    cursor = db.get_db_connection().cursor()
    cursor.execute(
        'SELECT id, username, full_name, is_admin, joined_at'
        ' FROM "user" WHERE id = %s', (user_id,)
    )
    user = cursor.fetchone()

    if not user:
        abort(404)

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
