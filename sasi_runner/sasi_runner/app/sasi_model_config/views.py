from sasi_runner.app import app
from sasi_runner.app.sasi_model_config.models import SASIModelConfig

from flask import Blueprint, request, jsonify, render_template, Markup


bp = Blueprint('sasi_model_config', __name__, url_prefix='/config',
               template_folder='templates') 

@bp.route('/', methods=['GET'])
def hello():
    return "hello" 

@bp.route('/<id>/edit', methods=['GET'])
def edit(id):
    # Load config model.
    config = SASIModelConfig(id)

    fields = [
        {
            'id': 'substrates',
            'label': 'Substrates'
        }
    ]

    # Render fields.
    rendered_fields = []
    for field in fields:
        rendered_field = get_rendered_field(field)
        rendered_fields.append(rendered_field)

    # Clobber assets.
    assets = {'css': {}, 'js': {}}
    for rendered_field in rendered_fields:
        field_assets = rendered_field.get('assets', {})
        for category, category_assets in assets.items():
            for asset in field_assets.get(category, []):
                category_assets[asset] = asset
    for category, category_assets in assets.items():
        assets[category] = assets[category].values()

    # Render template.
    return render_template("edit.html", config=config, assets=assets, 
                           fields=rendered_fields)

def get_rendered_field(field):
    content = """
    <h3>%s</h3>
    """ % field.get('label')
    return {
        'content': Markup(content),
        'assets': {
            'css': ['foo'],
            'js': ['bar']
        },
        'script': ''
    }
