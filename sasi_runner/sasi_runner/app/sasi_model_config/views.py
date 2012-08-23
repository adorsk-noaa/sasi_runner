from sasi_runner.app import app, db
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_file.views import sasi_file_to_dict

from flask import Blueprint, request, jsonify, render_template, Markup
from flask import url_for, json


bp = Blueprint('sasi_model_config', __name__, url_prefix='/config',
               template_folder='templates', static_folder='static') 

@bp.route('/', methods=['GET'])
def hello():
    return "hello" 

def render_reference_link(section=None):
    section_hash = ''
    if section:
        section_hash = '#%s' % section

    reference_link = """
    <a href="%s%s" target="_blank">SASI Configuration File Reference Guide</a>
    """ % (
        url_for('sasi_model_config.configuration_reference'),
        section_hash)
    
    return reference_link

@bp.route('/configuration_reference/', methods=['GET'])
def configuration_reference():
    return "fish"


@bp.route('/<id>/edit', methods=['GET'])
def edit(id):
    config = SASIModelConfig(id)

    # Initialize fields w/ title field.
    fields = [
        {
            'id': 'title', 
            'label': 'Title', 
            'widget': 'text',
            'description': "The name of this configuration."
        }
    ]

    # Define file select fields.
    file_select_fields = [
        'substrates',
        'features',
        'gears',
        'habitats',
        'grid',
        {'id': 'va', 'label': 'Vulnerability Assessment'},
        {'id': 'model_parameters', 'label': 'Model Parameters'},
        {'id': 'map_layers', 'label': 'Map Layers'},
        {'id': 'fishing_efforts', 'label': 'Fishing Efforts'}
    ]
    for field in file_select_fields:
        if isinstance(field, str):
            field = {'id': field} 
        field.setdefault('label', field['id'].capitalize())
        field.setdefault('widget', 'file_select')
        field.setdefault('widget_options',{'category': field['id']})
        field.setdefault('description', ('Select a file which contains '
                                         '%s data/metadata. See the %s '
                                         'for an example') % 
                         (field['label'], render_reference_link(field['id'])))
        fields.append(field)

    # Render fields.
    rendered_fields = []
    for field in fields:
        rendered_field = render_field(field)
        rendered_fields.append(rendered_field)

    # Initialize common assets.
    assets = get_common_assets()

    # Clobber assets from fields.
    clobbered_assets = {}
    for rendered_field in rendered_fields:
        for category, field_assets in rendered_field.get('assets', {}).items():
            asset_dict = clobbered_assets.setdefault(category, {})
            for field_asset in field_assets:
                asset_dict[field_asset] = field_asset

    # Add clobbered assets to global assets.
    for category, asset_dict in clobbered_assets.items():
        main_asset_set = assets.setdefault(category, [])
        main_asset_set.extend(asset_dict.keys())

    # Render template.
    return render_template("edit.html", config=config, assets=assets, 
                           fields=rendered_fields)

def render_field(field):
    rendered_widget = render_widget(field)

    html = rendered_widget.get('html')
    assets = rendered_widget.get('assets')
    script = rendered_widget.get('script')

    return {
        'id': field['id'],
        'label': field['label'],
        'description': Markup(field.get('description', '')),
        'html': Markup(html),
        'assets': {},
        'script': script
    }

def render_widget(field):
    widget_type = field.get('widget')

    if widget_type == 'text':
        return render_text_widget(field)

    elif widget_type == 'file_select':
        return render_file_select_widget(field)

def render_text_widget(field):
    script = render_template('js/text_widget.js', field=field)

    return {
        'script': script,
        'html': ('<div class="widget text"><label>%s: </label>'
                 '<input type="text" value="%s"></div>'
                ) % (field['label'], field.get('value', '')),
        'assets': {}
    }

def render_file_select_widget(field):
    # Get json for initial files.
    category = field['widget_options'].get('category')
    files = db.session.query(SASIFile).filter(SASIFile.category ==
                                              category).all()
    file_dicts = [sasi_file_to_dict(f) for f in files]
    files_json = json.dumps(file_dicts)

    script = render_template('js/file_select_widget.js',
                             field=field,
                             initial_files_json=files_json,
                             category=category
                            )
    return {
        'script': script,
        'html': '<div class="widget"></div>',
        'assets': {}
    }

def get_common_assets():
    return {
        'styles': [
            # SASIRunner.less
            format_link_asset(rel='stylesheet/less', href=url_for('static',
                filename='js/SASIRunner/src/styles/SASIRunner.less')),

            # SASIModelConfig_edit.less
            format_link_asset(rel='stylesheet/less',
                href=url_for('sasi_model_config.static', 
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


