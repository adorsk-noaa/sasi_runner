from sasi_runner.app import app, db
from sasi_runner.app.tasks.models import Task
from sasi_runner.app.tasks import util as tasks_util

from flask import Blueprint, jsonify


bp = Blueprint('tasks', __name__, url_prefix='/tasks',
               template_folder='templates', static_folder='static') 

@bp.route('/<int:task_id>/status', methods=['GET'])
def task_status(task_id):
    task = tasks_util.get_task(task_id)
    return jsonify(status=task.status, data=task.data)
