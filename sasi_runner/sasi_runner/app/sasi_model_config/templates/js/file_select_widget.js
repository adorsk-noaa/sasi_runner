require(["jquery","use!backbone","use!underscore", "SASIRunner"],
    function($, Backbone, _, SASIRunner){

        var sasi_files = new Backbone.Collection({{initial_files_json}});

        sasi_files.url = "{{ url_for('sasi_file.uploadCategoryFile', 
            category_id=category) }}";

        var sasi_file_select_model = new Backbone.Model({
            choices: sasi_files
        });

        var sasi_file_select_view = new SASIRunner.views.SASIFileTableSelectView({
            model: sasi_file_select_model,
            el: $('.field-section[id="{{field.id}}"] .widget')
        });

        sasi_file_select_model.on('change:selection', function(){
            var value = sasi_file_select_model.get('selection');
            fieldDispatcher.trigger('field:change', '{{field.id}}', value)
        });

        $(document).ready(function(){
            sasi_file_select_view.trigger('ready');
        });
    }
);
