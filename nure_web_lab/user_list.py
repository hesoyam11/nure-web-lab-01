from flask import (
    Blueprint, render_template
)

from . import db
from auth import login_required

bp = Blueprint('user_list', __name__, url_prefix='/users')


@bp.route('/')
@login_required
def get_list():
    cursor = db.get_db_connection().cursor()
    cursor.execute(
        'SELECT id, username, full_name, is_admin, joined_at'
        ' FROM "user" ORDER BY joined_at DESC'
    )
    users = cursor.fetchall()
    return render_template('user_list/user_list.html', users=users)
