from sasi_runner.app import app, db
from sasi_runner.app.sasi_model_config.models import SASIModelConfig
from sasi_runner.app.sasi_file.models import SASIFile
from sasi_runner.app.sasi_file.views import sasi_file_to_dict
from sasi_runner.app.sasi_model_config.util.run_config_task import (
    get_run_config_task)
from sasi_runner.app.tasks import util as tasks_util

from flask import Blueprint, request, jsonify, render_template, Markup
from flask import url_for, json, redirect

import futures as futures


bp = Blueprint('sasi_model_config', __name__, url_prefix='/config',
               template_folder='templates', static_folder='static') 

@bp.route('/', methods=['GET'])
def list_configs():
    configs = db.session.query(SASIModelConfig).all()
    assets = get_common_assets()

    # Setup actions.
    actions = [
        'edit',
        'run',
        'delete'
    ]

    for i in range(len(actions)):
        action = actions[i]
        actions[i] = {'id': action, 'label': action}

    actions.insert(2, {'id': 'clone', 'label': "clone as new"})

    return render_template("list_configs.html", configs=configs,
                           assets=assets, actions=actions) 

def render_reference_link(section=None):
    section_hash = ''
    if section:
        section_hash = '#%s' % section

    reference_link = """
    <a href="%s%s" target="_blank">SASI Configuration File Reference Guide</a>
    """ % (
        url_for('.configuration_reference'),
        section_hash)
    
    return reference_link

@bp.route('/configuration_reference/', methods=['GET'])
def configuration_reference():
    return "fish"

@bp.route('/<int:config_id>/pre_run', methods=['GET'])
def pre_run_config(config_id):
    assets = get_common_assets()
    return render_template("pre_run_config.html", assets=assets, 
                           config_id=config_id)

@bp.route('/<int:config_id>/run', methods=['POST'])
def run_config(config_id):
    """ Start config run task and redirect to status page for task. """
    output_format = request.form['output_format']
    task = get_run_config_task(
        config_id=config_id,
        output_format=output_format
    )
    tasks_util.makeTaskPersistent(task)
    task_id = task.id
    tasks_util.execute_task(task)
    return redirect(url_for('.run_status', task_id=task_id))

@bp.route('/run_status/<int:task_id>/', methods=['GET'])
def run_status(task_id):
    assets = get_common_assets()

    task = tasks_util.get_task(task_id)
    if not task:
        # Handle case when task does not exist.
        # @TODO: Flesh this out.
        return "No task!"
    else:
        stage_defs = {
            'validating': {'label': 'validating configuration...'},
            'metadata': {'label': 'generating metadata...'},
            'model': {'label': 'running model...'},
            'formatting': {'label': 'formatting results...'},
            'assembling': {'label': 'assembling output file...'},
        }
        json_stage_defs = json.dumps(stage_defs)

        task_status_data = {
            'status': {
                'code': task.status,
            },
            'stages': task.data.get('stages', {})
        }
        json_status = json.dumps(task_status_data)

        run_status_js = render_template(
            "js/run_status.js",
            task_id=task_id,
            json_status="{}",
            json_stage_defs=json_stage_defs
        )

        return render_template(
            "run_status.html", 
            assets=assets,
            task_id=task_id, 
            run_status_js=Markup(run_status_js)
        )

@bp.route('/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    config = initialize_config(config_id)
    db.session.delete(config)
    db.session.commit()
    return "deleted"

@bp.route('/', methods=['POST'], defaults={'config_id': None})
@bp.route('/<int:config_id>', methods=['POST'])
def save_config(config_id):
    config = initialize_config(config_id)

    # Update config w/ form values.
    for attr, value in request.form.items():
        if hasattr(config, attr):
            # If attribute is a file attribute,
            # get file from the db.
            if is_file_attr(attr):
                if value:
                    value = db.session.query(SASIFile).get(value)
                else:
                    value = None
            setattr(config, attr, value)

    # Save the config.
    db.session.add(config)
    db.session.commit()

    # Redirect to the configs page.
    return redirect(url_for('.list_configs'))

def is_file_attr(attr):
    """
    Helper function to determine if an attribute is a file
    attribute.
    """
    target_class = db.get_attr_target_class(
        SASIModelConfig, attr)
    return (target_class == SASIFile)

def initialize_config(config_id=None):
    """
    Helper function to load a config.
    """
    if not config_id:
        config = SASIModelConfig()
    else:
        config = db.session.query(SASIModelConfig).get(config_id)
    return config

@bp.route('/<int:config_id>/clone', methods=['GET'])
def clone(config_id=None):
    source_config = initialize_config(config_id)
    new_config = source_config.clone()
    new_config.title = "Clone of %s" % source_config.title
    return edit(config=new_config)

@bp.route('/create/', methods=['GET'], defaults={'config_id': None})
@bp.route('/<int:config_id>/edit', methods=['GET'])
def edit(config_id=None, config=None):
    if not config:
        config = initialize_config(config_id)

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
        {'id': 'energys', 'label': 'Energies'},
        'gears',
        'habitats',
        'grid',
        {'id': 'va', 'label': 'Vulnerability Assessment'},
        {'id': 'model_parameters', 'label': 'Model Parameters'},
        {'id': 'fishing_efforts', 'label': 'Fishing Efforts'},
        {'id': 'georefine', 'label': 'GeoRefine Data'}
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
        field.setdefault('value', getattr(config, field['id']))
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

    # Define post destination.
    form_url = url_for('.save_config', config_id=config_id)

    # Render template.
    return render_template("edit.html", config=config, assets=assets, 
                           fields=rendered_fields, form_url=form_url)

def render_field(field):
    rendered_widget = render_widget(field)

    html = rendered_widget.get('html')
    assets = rendered_widget.get('assets')
    script = rendered_widget.get('script')
    value = rendered_widget.get('value')

    return {
        'id': field['id'],
        'label': field['label'],
        'value': value,
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
        'assets': {},
        'value': field.get('value', '')
    }

def render_file_select_widget(field):
    # Get json for initial files.
    category = field['widget_options'].get('category')
    files = db.session.query(SASIFile).filter(SASIFile.category ==
                                              category).all()
    file_dicts = [sasi_file_to_dict(f) for f in files]
    files_json = json.dumps(file_dicts)

    selected_file = field.get('value')
    if selected_file:
        value = selected_file.id
    else:
        value = ''

    script = render_template('js/file_select_widget.js',
                             field=field,
                             initial_files_json=files_json,
                             category=category,
                             value=value
                            )

    return {
        'script': script,
        'html': '<div class="widget"></div>',
        'assets': {},
        'value': value
    }

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



