require(["jquery","use!backbone","use!underscore"],
    function($, Backbone, _){
        var $text = $('.field-section[id="{{field.id}}"] .widget input[type="text"]');

       $text.on('change', function(){
            var value = $text.val();
            if (value == ''){
                value = null;
            }
            fieldDispatcher.trigger('field:change', '{{field.id}}', value);
        });
    }
);
