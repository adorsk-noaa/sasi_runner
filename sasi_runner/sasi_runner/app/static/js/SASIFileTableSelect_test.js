require([
  "jquery",
  "use!backbone",
  "use!underscore",
  "_s",
  "use!ui",
  "SASIRunner"
],
function($, Backbone, _, _s, ui, SASIRunner){

    var fileCounter = 1;
    var createFileModel = function(opts){
        var fileModel = new Backbone.Model(_.extend({
            id: fileCounter,
            filename: fileCounter,
            size: Math.round(Math.random() * 1e5),
            created: new Date().toISOString()
        }, opts));
        fileCounter += 1;
        return fileModel;
    };

    // Create fake file models.
    var fileModels = [];
    for (var i = 0; i < 5; i++){
        var fileModel = createFileModel({
            id: i,
            filename: "file_" + i
        });
        fileModels.push(fileModel);
    }

    var sasi_files = new Backbone.Collection(fileModels);
    sasi_files.url = '/sasi_runner/sasi_file/category/testcat/';

	var sasi_file_select_model = new Backbone.Model({
        choices: sasi_files
    });

    var columns = [];
    _.each(['filename', 'size', 'created'], function(attr){
        columns.push({
            field: attr,
            label: attr
        });
    });
	var sasi_file_select_view = new SASIRunner.views.SASIFileTableSelectView({
		model: sasi_file_select_model,
		el: $("#main"),
        columns: columns
    });

	$(document).ready(function(){
        console.log("document.ready");
        sasi_file_select_view.trigger('ready');
	});

});
