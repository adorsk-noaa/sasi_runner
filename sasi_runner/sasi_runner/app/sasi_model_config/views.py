from sasi_runner.app import app
from sasi_runner.app.sasi_model_config.models import SASIModelConfig

from flask import Blueprint, request, jsonify, render_template, Markup, url_for


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
        rendered_field = render_field(field)
        rendered_fields.append(rendered_field)

    # Initialize assets with common assets.
    assets = get_common_assets()

    # Clobber assets from fields.
    # @TODO: set this from asset categories above.
    clobbered_assets = {}
    for rendered_field in rendered_fields:
        for asset in rendered_field.get('assets', []):
            clobbered_assets[asset] = asset

    # Add clobbered assets to global assets.
    assets.extend(clobbered_assets.keys())

    # Render template.
    return render_template("edit.html", config=config, assets=assets, 
                           fields=rendered_fields)

def render_field(field):
    content = """
    <div class="field-section" id="%s">
    <h3 class="header">%s</h3>
    <div class="body">
    <div class="description">The description</div>
    <div class="widget">The Widget</div>
    </div>
    </div>
    """ % (field.get('id'), field.get('label'))

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

            $(document).ready(function(){
                sasi_file_select_view.trigger('ready');
            });
        });
    """ % (field.get('id'))
    return {
        'content': Markup(content),
        'assets': [],
        'script': script
    }

def get_common_assets():
    return [
        # require.js
        format_script_asset(src=url_for('static', filename='js/require_config.js')),

        format_script_asset(src=url_for('static',
                                    filename='sasi_assets/js/require.js/require.js')),

        # SASIRunner.less
        format_link_asset(rel='stylesheet/less', href=url_for('static',
            filename='js/SASIRunner/src/styles/SASIRunner.less')),

        # less.js
        format_script_asset(src=url_for('static', filename='sasi_assets/js/less.js')),

        # jquery-ui css
        format_link_asset(rel='stylesheet/less', href=url_for('static',
            filename='sasi_assets/js/jquery.ui/styles/jquery-ui-1.8.18.custom.css'))
    ]

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


