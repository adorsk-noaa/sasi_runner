define([
	"jquery",
	"use!backbone",
	"use!underscore",
	"use!ui",
	"_s",
	"use!qtip",
	"use!jqForm",
	"TableSelect",
	"text!./templates/AddFileDialog.html",
		],
function($, Backbone, _, ui, _s, qtip, jqForm, TableSelect, AddFileDialogTemplate){

    var TableSelectView = TableSelect.views.TableSelectView;

	var SASIFileTableSelectView = TableSelectView.extend({
		initialize: function(opts){

            $(this.el).addClass('sasi-file-table-select');

            // Set columns for files.
            var fileColumns = [];
            _.each(['filename', 'size', 'created'], function(attr){
                fileColumns.push({
                    field: attr,
                    label: attr
                });
            });
            opts.columns = fileColumns;

            // Use 'filename' as the selection label attribute.
            opts.selectionLabelAttr = 'filename';

            // Create 'add file' control.
            var $fileControl = this.createAddFileControl();
            opts.controls = [$fileControl];

            TableSelectView.prototype.initialize.apply(this, arguments);
            this.postInitialize();
        },

        postInitialize: function(){
            TableSelectView.prototype.postInitialize.apply(this, arguments);
        },

        createAddFileControl: function(){
            var _this = this;
            var $fileControl = $('<div class="add-file-control"><div class="add-file-button">add new file...</div></div>');
            var $fileDialog = $(_.template(AddFileDialogTemplate, {}));
            var $dialogLauncher = $('.add-file-button', $fileControl);
            var $cancelButton = $('.cancel', $fileDialog);
            var $submitButton = $('.submit', $fileDialog);
            var $form = $('.upload-form', $fileDialog);
            var $overlay = $('.overlay', $fileDialog);
            var $loadingStatus = $('.loading-status', $fileDialog);
            var $loadingText = $('.text', $loadingStatus);
            var $loadingImg = $('.image', $loadingStatus);

            // Set up dialog.
            $dialogLauncher.qtip({
                content: {
                    text: $fileDialog,
                    title: {
                        text: 'Add new file',
                        button: false
                    },
                },
                position: {
                    my: 'left top',
                    at: 'left bottom',
                    adjust: {
                        y: 10
                    }
                },
                show: {
                    event: 'click'
                },
                hide: {
                    fixed: true,
                    event: 'unfocus'
                },
                style: {
                    classes: 'add-file-dialog',
                    tip: false
                },
                events: {
                    render: function(event, api) {
                        // Toggle when target is clicked.
                        $(api.elements.target).on('click', function(clickEvent){
                            clickEvent.stopPropagation();
                            clickEvent.stopImmediatePropagation();
                            api.toggle();
                        });
                    },

                    hide: function(event, api){
                        if (_this.uploading){
                            event.preventDefault();
                        }
                    },

                    hidden: function(event, api){
                        // Clear file dialog form.
                        $form[0].reset();
                        $loadingStatus.removeClass('success error');
                        $loadingText.html('');
                    }
                }
            });


            // Close dialog on when cancel button is clicked.
            $cancelButton.on('click', function(event){
                console.log("click cancel");
                $dialogLauncher.qtip('api').hide()
            });

            // Submit upload when submit button is clicked.
            $submitButton.on('click', function(event){

                var deferred = $.Deferred();
                $submitButton.attr('disabled', true);
                $cancelButton.attr('disabled', true);
                _this.uploading = true;
                $loadingText.html('uploading...');
                $loadingImg.animate({opacity: 1});
                $overlay.fadeIn(function(){
                    $form.ajaxSubmit({
                    url: _this.choices.url,
                    type: 'POST',
                    iframe: true,
                    dataType: 'json',
                    success: function(data){
                    deferred.resolve(data);
                    },
                    error: function(){
                    deferred.reject();
                    }
                    });

                    /*
                    setTimeout(function(){
                        var fakeModel = {
                            id: Math.random(),
                            filename: 'foo'
                        };
                        deferred.resolve(fakeModel);
                    }, 1500);
                    */
                });

                // When upload completes successfully, create file model from response.
                deferred.done(function(data){
                    $overlay.fadeOut(function(){
                        $loadingText.html('Upload was successful.');
                        $loadingStatus.addClass('success');
                        var fileModel = new Backbone.Model(data);
                        _this.choices.add(fileModel);
                    });
                });

                // Handle errors.
                deferred.fail(function(error){
                    $overlay.fadeOut(function(){
                        $loadingText.html('Upload error: ' + error);
                        $loadingStatus.addClass('error');
                    });
                });

                // To be executed for both success/failure.
                deferred.always(function(){
                    $loadingImg.animate({opacity: 0});
                    _this.uploading = false;
                    $submitButton.attr('disabled', false);
                    $cancelButton.attr('disabled', false);
                });



            });
            return $fileControl;
        }
    });

	return SASIFileTableSelectView;
});
		

