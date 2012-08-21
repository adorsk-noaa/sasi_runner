from sasi_runner.app import app, db
from sasi_runner.config import config as sr_config
from sasi_runner.app.sasi_file.models import SASIFile

from flask import Blueprint, request, Response, json, jsonify, render_template
from flask import Markup, url_for
from flaskext.uploads import UploadSet, ARCHIVES, TEXT, IMAGES
import os
from datetime import datetime


bp = Blueprint('sasi_file', __name__, url_prefix='/sasi_file',
               template_folder='templates') 

uploads_dest = os.path.join(sr_config['STORAGE_ROOT'], 'sasi_file')
uploads = UploadSet('sasifile', extensions=ARCHIVES + TEXT + IMAGES,
    default_dest=lambda app: uploads_dest)

upload_sets = [uploads]


@bp.route('/', methods=['GET'])
def hello():
    return "hello sasi file" 

@bp.route('/category/<categoryId>/', methods=['POST'])
def uploadCategoryFile(categoryId):
    if 'sasi_file' in request.files:
        filename = uploads.save(request.files['sasi_file'])
        # Get file info.
        path = uploads.path(filename)
        size = os.stat(path).st_size
        # Create file model.
        sasi_file = SASIFile(filename=filename, category=categoryId, path=path, 
                             size=size, created=datetime.utcnow())
        db.session.add(sasi_file)
        db.session.commit()

        # Return jsonified file.
        file_dict = sasi_file_to_dict(sasi_file)
        return jsonify(file_dict)

@bp.route('/category/<categoryId>/', methods=['GET'])
def getCategoryFiles(categoryId):
    category_files = db.session.query(SASIFile).filter(SASIFile.category ==
                                                       categoryId)
    file_dicts = []
    for category_file in category_files:
        file_dicts.append(sasi_file_to_dict(category_file))

    return Response(json.dumps(file_dicts, indent=2), mimetype='application/json')

def sasi_file_to_dict(sasi_file):
    file_dict = {}
    for attr in ['id', 'filename', 'category', 'size', 'created']:
        value = getattr(sasi_file, attr, None)
        if isinstance(value, datetime):
            value = value.isoformat()
        file_dict[attr] = value
    return file_dict

@bp.route('/uploadForm', methods=['GET'])
def uploadForm():
    html = """
    <form method=POST enctype=multipart/form-data action="%s">
    <input type=file name=sasi_file>
    <input type=submit name=submit>
    </form>
    """ % url_for('sasi_file.uploadTest')
    return Markup(html)
