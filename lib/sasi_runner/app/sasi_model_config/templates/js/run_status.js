require(["jquery","use!backbone","use!underscore", "TaskStatus"],
function($, Backbone, _, TaskStatus){
    var POLLING_INTERVAL = 5000;

    // Setup tracker.
    
    var stage_defs = {{json_stage_defs}};

    var stages = new Backbone.Collection();
    _.each(stage_defs, function(stage_def){
        var stage = new Backbone.Model(stage_def);
        stages.add(stage);
    });

    var status = new Backbone.Model({{json_status}});

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
            'code': taskData.status
        };

        if (status.code == 'rejected'){
            status.msg = taskData.data.error;
        }

        tracker_model.get('status').set(status);

        // Set states.
        var tracker_stages = tracker_model.get('stages');
        _.each(taskData.data.stages, function(stage_data, stage_id){
            stageModel = tracker_stages.get(stage_id);
            console.log("sm is: ", stageModel);
            if (! stageModel){
                tracker_stages.add(new Backbone.Model(stage_data));
            }
            else{
                console.log("here");
                stageModel.get('status').set(stage_data.status);
            }
        });
    };

    var handleGetTaskStatusError = function(xhr, status, error){
        console.log("error!", arguments);
    };

    var processTaskStatus = function(taskData){
        if (taskData.status == 'resolved'){
            // Do completion stuff here.
        }
        else if (taskData.status == 'rejected'){
            console.log('rejected!');
        }
        else{
            setTimeout(getTaskStatus, POLLING_INTERVAL);
        }
        updateTracker(taskData);
    };

    // If the task is not completed, kick things off by 
    // fetching the task status.
    if (tracker_model.get('status').get('code') != 'completed'){
        getTaskStatus();
    }
});
