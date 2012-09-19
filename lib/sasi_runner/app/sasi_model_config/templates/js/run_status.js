require(["jquery","use!backbone","use!underscore", "_s", "TaskStatus"],
function($, Backbone, _, _s, TaskStatus){
    var POLLING_INTERVAL = 3000;

    // Initial data.
    var stage_defs = {{json_stage_defs}};
    var initial_task_data= {{json_initial_task_data}};
    var initialized = false;

    // Setup tracker.
    var stages = new Backbone.Collection();
    _.each(stage_defs, function(stage_def){
        var stage = new Backbone.Model(stage_def);
        stages.add(stage);
    });

    var status = new Backbone.Model();

    var tracker_model = new Backbone.Model({
        status: status,
        stages: stages
    });

    var tracker_view = new TaskStatus.views.TaskStatusTrackerView({
        el: $('.run-status-tracker'),
        model: tracker_model
    });

    var getTaskStatus = function(){
        var deferred = $.ajax({
            url: "{{ url_for('tasks.task_status', task_id=task_id) }}",
            type: 'GET',
            error: handleGetTaskStatusError,
            success: processTaskStatus
        });
        return deferred;
    };

    var updateTracker = function(taskData){
        // Set status.
        var status = {
            'code': taskData.status,
            'progress': taskData.data.progress,
        };

        if (status.code == 'rejected'){
            status.msg = taskData.data.error;
        }

        else if (status.code == 'resolved'){
            status.msg = taskData.data.success_msg;
        }

        tracker_model.get('status').set(status);

        // Set states.
        var tracker_stages = tracker_model.get('stages');
        _.each(taskData.data.stages, function(stage_data, stage_id){
            stageModel = tracker_stages.get(stage_id);
            if (! stageModel){
                tracker_stages.add(new Backbone.Model(stage_data));
            }
            else{
                stageModel.get('status').set(stage_data.status);
            }
        });
    };

    var handleGetTaskStatusError = function(xhr, status, error){
        console.log("error!", arguments);
    };

    var processTaskStatus = function(taskData){
        var deferred = $.Deferred();
        if (taskData.status == 'resolved'){
            var result_file = taskData.data.result_file;
            var file_name = result_file.filename;
            var file_link_template = "{{url_for('sasi_file.download_file', file_id=-99999) }}";
            var file_link = file_link_template.replace('-99999', result_file.id);
            var files_page_link = "{{url_for('sasi_file.list_files')}}";
            var msg = _s.sprintf(
                '<p>Your results file is ready for download: ' + 
                '<a href="%s">%s</a></p>',
                file_link, file_name);
            msg += _s.sprintf(
                '<p>If you want to delete this result, visit the ' + 
                '<a href="%s">files page</a>.</p>',
                files_page_link);
            taskData.data.success_msg = msg;
            deferred.resolve(taskData);
        }
        else if (taskData.status == 'rejected'){
            deferred.resolve(taskData);
        }
        else{
            if (initialized){
                setTimeout(getTaskStatus, POLLING_INTERVAL);
            }
            else{
                initialized = true;
                getTaskStatus();
            }
            deferred.resolve(taskData);
        }

        deferred.done(function(data){
            updateTracker(data);
        });
    };

    // Process initial task data to kick things off.
    processTaskStatus(initial_task_data);
});
