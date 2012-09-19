from sasi_runner.app import app, db
from sasi_runner.app import util as app_util
from sasi_runner.config import config as sr_config
from sasi_runner.app.sasi_file.models import SASIFile

from flask import Blueprint, request, Response, json, jsonify, render_template
from flask import Markup, url_for, redirect
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
@bp.route('/category/<category_id>/', methods=['GET'])
def list_files(category_id=None):
    q = db.session.query(SASIFile)
    if category_id:
        q = q.filter(SASIFile.category == category_id)
    files = q.all()

    file_dicts = []
    for f in files:
        file_dicts.append(sasi_file_to_dict(f))

    # JSON.
    if app_util.request_wants_json():
        return Response(
            json.dumps(file_dicts, indent=2), 
            mimetype='application/json'
        )
    
    # Page.
    else:
        assets = get_common_assets()
        actions = [
            'delete'
        ]
        for i in range(len(actions)):
            action = actions[i]
            actions[i] = {'id': action, 'label': action}

        return render_template(
            "files_list.html", 
            file_dicts=file_dicts,
            assets=assets, 
            actions=actions
        ) 

@bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    f = initialize_file(file_id)
    if f:
        db.session.delete(f)
        db.session.commit()
        return "deleted"
    #@TODO: 404 this.
    return "File does not exist."

@bp.route('/<int:file_id>/download', methods=['GET'])
def download_file(file_id):
    f = initialize_file(file_id)
    if f:
        return redirect(get_file_download_url(f))
    else:
        #@TODO: 404 this.
        return "File does not exist."

@bp.route('/category/<category_id>/file/', methods=['POST'])
def uploadCategoryFile(category_id):
    if 'sasi_file' in request.files:
        filename = uploads.save(request.files['sasi_file'])
        # Get file info.
        path = uploads.path(filename)
        size = os.stat(path).st_size
        # Create file model.
        sasi_file = SASIFile(filename=filename, category=category_id, path=path, 
                             size=size, created=datetime.utcnow())
        db.session.add(sasi_file)
        db.session.commit()

        # Return jsonified file.
        file_dict = sasi_file_to_dict(sasi_file)
        return jsonify(file_dict)

@bp.route('/category/<category_id>/', methods=['GET'])
def getCategoryFiles(category_id):
    category_files = db.session.query(SASIFile).filter(SASIFile.category ==
                                                       category_id)
    file_dicts = []
    for category_file in category_files:
        file_dicts.append(sasi_file_to_dict(category_file))

    return Response(json.dumps(file_dicts, indent=2), mimetype='application/json')

def get_file_download_url(sasi_file):
    saved_filename = os.path.basename(sasi_file.path)
    return uploads.url(saved_filename)

def sasi_file_to_dict(sasi_file):
    file_dict = sasi_file.to_dict()
    file_dict['url'] = get_file_download_url(sasi_file)
    return file_dict

@bp.route('/file/<file_id>/', methods=['GET'])
def getFileData(file_id):
    f = db.session.query(SASIFile).get(file_id)
    file_dict = sasi_file_to_dict(f)
    return jsonify(file_dict)

def get_common_assets():
    return {
        'styles': [
            # jquery-ui css
            app_util.format_link_asset(rel='stylesheet', href=url_for('static', 
                filename=('sasi_assets/js/jquery.ui/styles/'
                          'jquery-ui-1.8.18.custom.css')))
        ],

        'scripts': [
            # require.js
            app_util.format_script_asset(src=url_for('static', 
                filename='js/require_config.js')),

            app_util.format_script_asset(src=url_for('static',
                filename='sasi_assets/js/require.js/require.js')),
        ],

    }

def initialize_file(file_id=None):
    """
    Helper function to load a file.
    """
    f = db.session.query(SASIFile).get(file_id)
    return f
