from sasi_runner.app import app
from sasi_runner.app.sasi_model_config.models import SASIModelConfig

from flask import Blueprint, request, jsonify, render_template, Markup, url_for


bp = Blueprint('sasi_model_config', __name__, url_prefix='/config',
               template_folder='templates', static_folder='static') 

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
            'label': 'Substrates',
            'description': '''
            Select a file which contains SASI substrate data/metadata. See blabla for examples...
            '''
        }
    ]

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
    body= """
    <div class="widget">The Widget</div>
    """

    script = """
        require(["jquery","use!backbone","use!underscore", "SASIRunner"],
        function($, Backbone, _, SASIRunner){
            var sasi_files = new Backbone.Collection();
            sasi_files.url = '/sasi_runner/sasi_file/category/testcat/';

            var sasi_file_select_model = new Backbone.Model({
                choices: sasi_files
            });

            var sasi_file_select_view = new SASIRunner.views.SASIFileTableSelectView({
                model: sasi_file_select_model,
                el: $('.field-section[id="%s"] .widget')
            });
            
            sasi_file_select_model.on('change:selection', function(){
                var value = sasi_file_select_model.get('selection');
                fieldDispatcher.trigger('field:change', '%s', value)
            });

            $(document).ready(function(){
                sasi_file_select_view.trigger('ready');
            });
        });
    """ % (field.get('id'), field.get('id'))
    return {
        'id': field.get('id'),
        'label': field.get('label'),
        'description': field.get('description'),
        'body': Markup(body),
        'assets': {},
        'script': script
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


