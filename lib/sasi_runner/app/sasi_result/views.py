from sasi_runner.app import app, db
from sasi_runner.app.sasi_result import models as sr_models

from flask import Blueprint, request, jsonify, render_template, Markup
from flask import url_for, json, redirect


bp = Blueprint('sasi_result', __name__, url_prefix='/results',
               template_folder='templates', static_folder='static') 

@bp.route('/', methods=['GET'])
def list_results():
    results = db.session.query(sr_models.SASIResult).all()
    assets = get_common_assets()

    # Setup actions.
    actions = [
        'delete'
    ]

    for i in range(len(actions)):
        action = actions[i]
        actions[i] = {'id': action, 'label': action}

    return render_template("list_results.html", results=results,
                           assets=assets, actions=actions) 


@bp.route('/<result_id>', methods=['DELETE'])
def delete_result(result_id):
    #@TODO DO DELETE STUFF HERE.
    return "deleted"

def get_common_assets():
    return {
        'styles': [
            # SASIRunner.less
            format_link_asset(rel='stylesheet/less', href=url_for('static',
                filename='js/SASIRunner/src/styles/SASIRunner.less')),

            # SASIModelConfig_edit.less
            format_link_asset(rel='stylesheet/less',
                href=url_for('.static', 
                             filename='styles/SASIModelConfig_edit.less')), 
            # jquery-ui css
            format_link_asset(rel='stylesheet', href=url_for('static', 
                filename=('sasi_assets/js/jquery.ui/styles/'
                          'jquery-ui-1.8.18.custom.css')))
        ],

        'scripts': [
            # require.js
            format_script_asset(src=url_for('static', 
                filename='js/require_config.js')),

            format_script_asset(src=url_for('static',
                filename='sasi_assets/js/require.js/require.js')),
        ],

    }

def format_script_asset(type_='text/javascript', **kwargs):
    asset = '<script '
    for key, value in kwargs.items() + [('type', type_)]:
        asset += '%s="%s" ' % (key, value)
    asset += '></script>'
    return Markup(asset)

def format_link_asset(rel='stylesheet', type_='text/css', **kwargs):
    asset = '<link '
    for key, value in kwargs.items() + [('rel', rel), ('type', type_)]:
        asset += '%s="%s" ' % (key, value)
    asset += '>'
    return Markup(asset)



