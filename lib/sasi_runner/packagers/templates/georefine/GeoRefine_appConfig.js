(function(){

  var setUpSasiConfig = function($, Backbone, _, _s){

    var resolutions = [156543.033928, 78271.5169639999, 39135.7584820001, 19567.8792409999, 9783.93962049996, 4891.96981024998, 2445.98490512499, 1222.99245256249, 611.49622628138, 305.748113140558, 152.874056570411, 76.4370282850732, 38.2185141425366, 19.1092570712683, 9.55462853563415, 4.77731426794937, 2.38865713397468];

    var commonLayerDefs = [
      {
      layer_type:"Graticule",
      label:"Lat/Lon Grid",
      zIndex: 50,
      properties: {
        visibility: false,
      }
    },
      {% for layer in layers -%}
      {% if layer.json_config -%}
      {= layer.json_config =},
      {% endif -%}
      {% endfor -%}
    ];

    var defaultLayerProperties = {
      transitionEffect:"resize",
      opacity: .75,
    };
    {% if map_config.defaultLayerProperties -%}
    $.extend(true, defaultLayerProperties, {= map_config.defaultLayerProperties =});
    {% endif -%}

    var defaultMapProperties = {
      maxExtent: [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
      extent: [-7792364.354444444, 3503549.8430166757, -7235766.900555555, 6446275.8401198285],
      resolutions: [4891.96981024998, 2445.98490512499, 1222.99245256249, 611.49622628138, 305.748113140558, 152.874056570411],
      allOverlays: true,
      projection: 'EPSG:3857',
      displayProjection: 'EPSG:4326',
    };
    {% if map_config.defaultMapProperties -%}
    $.extend(true, defaultMapProperties, {= map_config.defaultMapProperties =});
    {% endif -%}

    var cellsFeatureQuery = new Backbone.Model({
      ID: 'features',
      SELECT: [
        {ID: 'fid', EXPRESSION: '__cell__id'},
        {
          ID: 'geometry',
          EXPRESSION: 'func.AsGeoJSON(func.SimplifyPreserveTopology(__cell__geom, 100))',
        },
      ]
    });


    var generateListFacetModel = function(opts){
      var field = opts.field;
      var modelOpts = {};
      var idId = field.idId || field.id + '_id';
      var labelId = field.labelId || field.id + '_label';
      var keyTable = field.keyTable || field.id;
      var idCol = field.idCol || 'id';
      var labelCol = field.labelCol || 'label';
      var tableCol = field.tableCol || field.id + '_id';
      var tableColExpression = field.tableColExpression || '__' + opts.table + '__' + tableCol;
      var idColExpression = field.idColExpression || '__' + keyTable + '__' + idCol;
      var labelColExpression = field.labelColExpression || '__' + keyTable + '__' + labelCol;
      var infoLink = "{{PROJECT_STATIC_DIR}}/sasipedia/index.html#" + field.sasipediaId + '/index.html' || field.infoLink;

      $.extend(true, modelOpts, {
        infoLink: infoLink,
        inner_query: {
          SELECT: [
            {EXPRESSION: tableColExpression, ID: idId}
          ],
          GROUP_BY: [
            {ID: idId}
          ],
        },
        outer_query: {
          SELECT: [
            {EXPRESSION: idColExpression, ID: idId},
            {EXPRESSION: labelColExpression, ID: labelId}
          ],
          FROM: [
            {
            SOURCE: keyTable,
            JOINS: [
              [
                "inner",
                [
                  {TYPE: "ENTITY", EXPRESSION: "__inner__" + idId}, "==",
                  {TYPE: "ENTITY", EXPRESSION: idColExpression}
                ]
            ]
            ]
          }
          ],
          GROUP_BY: [
            {ID: labelId},
            {ID: idId}
          ],
        },
        KEY: {
          LABEL_ENTITY: {ID: labelId},
          QUERY: {
            SELECT: [
              {EXPRESSION: idColExpression, ID: idId},
              {EXPRESSION: labelColExpression, ID: labelId}
            ]
          },
          KEY_ENTITY: {EXPRESSION: tableColExpression, ID: idId}
        },
        label: field.label,
        type: "list",
        filter_entity: {TYPE: "ENTITY", EXPRESSION: tableColExpression, ID: field.id},
        base_filter_groups: ["scenario"],
        primary_filter_groups: ["data"]
      }, field);

      return new Backbone.Model(modelOpts);
    };

    var generateDataLayerDef = function(opts){
      var field = opts.field;
      var densityId = field.col + '_density';
      var propertyMappings = [
        {source: densityId, target: densityId, default: 0.0},
      ];

      var scaleOpts = {};
      scaleOpts.scale_type = field.scale_type;
      if (scaleOpts.scale_type == 'sequential'){
        scaleOpts.vmin = 0;
        scaleOpts.vmax = 1;
      }
      else if (scaleOpts.scale_type == 'diverging'){
        scaleOpts.vmid = field.scale_mid;
        scaleOpts.vr = 1;
      }

      var modelOpts = {};
      $.extend(true, modelOpts, scaleOpts, {
        id: field.id,
        colormapId: field.colormapId,
        dataProp: densityId,
        layer_type: 'Vector',
        layer_category: 'data',
        source: 'georefine_data',
        label: field.label + ', per unit cell area',
        zIndex: 40,
        properties: {
          visibility: true,
          projection: 'EPSG:3857',
          preFeatureInsert: '(function(feature){feature.geometry.transform("EPSG:4326", "EPSG:3857")})',
        },
        expanded: true,
        base_filter_groups: ['scenario'],
        primary_filter_groups: ['data'],
        featuresQuery: cellsFeatureQuery,
        propertiesQuery: new Backbone.Model({
          quantity_field: new Backbone.Model({
            inner_query: {
              SELECT: [
                {ID: field.col + '_sum', EXPRESSION: 'func.sum(__' + opts.table + '__' + field.col + ')'},
                {ID: 'cell_id', EXPRESSION: '__' + opts.table + '__cell_id'}
              ],
              GROUP_BY: [
                {ID: 'cell_id'}
              ]
            },
            outer_query: {
              SELECT: [
                {ID: field.col + '_density', EXPRESSION: '__inner__' + field.col + '_sum/__cell__area'},
                {ID: 'cell_id', EXPRESSION: '__cell__id'},
              ],
              FROM: [
                {
                SOURCE: 'cell',
                JOINS: [
                  ['inner', [{TYPE: 'ENTITY', EXPRESSION: '__inner__cell_id'}, 
                    '==', {TYPE: 'ENTITY', EXPRESSION: '__cell__id'}, ] ]
                ]
              }
              ]
            },
          }),
          KEY: new Backbone.Model({
            KEY_ENTITY: {
              EXPRESSION: '__' + opts.table + '__cell_id',
              ID: 'cell_id',
              ALL_VALUES: true
            },
            QUERY: {
              ID: 'kq',
              SELECT: [
                {ID: 'cell_id', EXPRESSION: '__cell__id'},
              ]
            }
          }),
          mappings: propertyMappings,
        }),
        styleMap: new Backbone.Collection(
          [
            new Backbone.Model({
          id: 'default',
          strokeWidth: .1,
        })
        ])
      });

      $.extend(true, modelOpts, field);
      return modelOpts;
    };

    var generateInitialActions = function(field){
      var initialTimestepFacetActionQueue = {
        async: false,
        type: "actionQueue",
        once: true,
        actions: [
          {
          handler: "facets_facet_add",
          type: "action",
          opts: {
            category: "base",
            fromDefinition: true,
            definitionId: "time",
            facetId: "time",
          }
        },
        {
          handler: "facets_facet_initialize",
          type: "action",
          opts: {
            category: "base",
            id: "time"
          }
        },
        {
          handler: "facets_facet_connect",
          type: "action",
          opts: {
            category: "base",
            id: "time"
          }
        },
        {
          handler: "facets_facet_getData",
          type: "action",
          opts: {
            category: "base",
            id: "time"
          }
        },
        {
          handler: "facets_facet_setSelection",
          type: "action",
          opts: {
            category: "base",
            index: {=initial_tstep_index|default(1)=},
            id: "time"
          }
        }
        ]
      };

      var initialSummaryBarActionQueue = {
        async: false,
        type: "actionQueue",
        once: true,
        actions: [
          {
          handler: "summaryBar_initialize",
          type: "action"
        },
        {
          handler: "summaryBar_connect",
          type: "action"
        },
        {
          handler: "summaryBar_updateQuery",
          type: "action"
        },
        {
          handler: "summaryBar_getData",
          type: "action",
        }
        ]
      };

      var mapActionQueue = {
        async: false,
        type: "actionQueue",
        actions: [
          {
          type: "action",
          handler: "mapEditor_initializeMapEditor"
        },
        {
          type: "action",
          once: true,
          handler: "mapEditor_zoomToLayerDataExtent",
          opts: {
            layerId: field.id,
          }
        },
        ]
      };

      var summaryBarActionQueue = {
        async: false,
        type: "actionQueue",
        actions: [
          {
          handler: "summaryBar_initialize",
          type: "action"
        },
        {
          handler: "summaryBar_connect",
          type: "action"
        },
        ]
      };

      var facetsEditorActionQueue = {
        async: false,
        type: "actionQueue",
        actions: [
          {
          type: "action",
          handler: "facetsEditor_connect"
        },
        ]
      };

      var initialActions = {
        async: false,
        type: "actionQueue",
        actions: [
          initialTimestepFacetActionQueue,
          initialSummaryBarActionQueue,
          summaryBarActionQueue,
          facetsEditorActionQueue,
          mapActionQueue,
        ]
      };

      return initialActions;
    };

    var generateDataViewConfigs = function(opts){
      var qFields = {};
      _.each(opts.fields, function(field){
        if (! field.col){
          field.col = field.id;
        }
        var modelOpts = {};

        var entityId = field.id + '_sum';
        $.extend(true, modelOpts, {
          id: field.id,
          label: field.label,
          format: '%.1H',
          inner_query: {
            SELECT: [{ID: entityId, EXPRESSION: 'func.sum(__' + opts.table + '__' + field.col + ')'}]
          },
          outer_query: {
            SELECT: [{ID: entityId + '_sum', EXPRESSION: '__inner__' + entityId}]
          },
        }, field);
        qFields[field.id] = new Backbone.Model(modelOpts);
      });

      var facetDefinitions = new Backbone.Collection();

      // Timestep facet.
      var timeFacetOpts = {
        id: 'time',
        label: 'Time',
        noClose: true,
        noMenu: true,
        primary_filter_groups: ['scenario'],
        type: 'timeSlider',
        value_type: 'numeric',
        filter_entity: {
          EXPRESSION: '__' + opts.table + '__t',
          ID: 't',
          TYPE: 'ENTITY'
        },
        KEY: {
          KEY_ENTITY: {EXPRESSION: '__' + opts.table + '__t', ID: 't'},
          QUERY: {
            SELECT: [{EXPRESSION: '__time__id', 'ID': 't'}]
          }
        },
      };
      facetDefinitions.add(new Backbone.Model(timeFacetOpts));

      _.each(opts.facetFields, function(field){
        facetDefinitions.add(generateListFacetModel({
          field: field,
          table: opts.table,
        }));
      });

      var dataLayerDefs = {};
      _.each(opts.fields, function(field){
        dataLayerDefs[field.id] = generateDataLayerDef({
          field: field,
          table: opts.table,
        });
      });

      var dvConfigs = [];
      _.each(opts.fields, function(field){

        // Setup layers.
        var layers = new Backbone.Collection();
        var dataLayerDef = dataLayerDefs[field.id];
        _.each(commonLayerDefs.concat([dataLayerDef]), function(layerDef){
          var mergedProps = {};
          $.extend(true, mergedProps, defaultLayerProperties, layerDef.properties);
          var layerModel = new Backbone.Model(layerDef);
          layerModel.set('properties', new Backbone.Model(mergedProps));
          layers.add(layerModel);
        });

        dvConfigs.push(new Backbone.Model({
          label: field.label,
          qField: qFields[field.id],
          filterGroups: ['scenario', 'data'],
          summaryBar: new Backbone.Model({
            base_filter_groups: ['scenario'],
            primary_filter_groups: ['data'],
          }),
          facetsEditor: new Backbone.Model({
            facetDefinitions: facetDefinitions,
            facets: new Backbone.Collection([])
          }),
          mapEditor: new Backbone.Model({
            map: new Backbone.Model({
              properties: new Backbone.Model(defaultMapProperties)
            }),
            layers: layers,
          }),
          initialActions: generateInitialActions(field),
        }));
      });

      return dvConfigs;
    };

    /**************/


    /**************/
    var generateSasiResultConfigs = function(){
      var dvConfigs = generateDataViewConfigs({
        table: 'sasi_result',
        fields: [
          {
          id: 'a',
          label: 'Applied Swept Area (A)',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
          format: '%.1H km<sup>2</sup>',
        },
        {
          id: 'y',
          label: 'Modified Swept Area (Y)',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
          format: '%.1H km<sup>2</sup>',
        },
        {
          id: 'x',
          label: 'Recovered Area (X)',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:G',
          format: '%.1H km<sup>2</sup>',
        },
        {
          id: 'z',
          label: 'Instantaneous Net Swept Area (Z = X - Y)',
          scale_type: 'diverging',
          scale_mid: 0,
          colormapId: 'ColorBrewer:PiG',
          format: '%.1H km<sup>2</sup>',
        },
        {
          id: 'znet',
          label: 'Cumulative Net Swept Area',
          scale_type: 'diverging',
          scale_mid: 0,
          colormapId: 'ColorBrewer:PiG',
          format: '%.1H km<sup>2</sup>',
        },
        ],
        facetFields: [
          {% if 'substrate_id' in result_fields %}
          {
          id: 'substrate',
          sasipediaId: 'substrates',
          label: "Substrates",
        },
          {% endif %}
          {% if 'energy_id' in result_fields %}
        {
          id: 'energy',
          sasipediaId: 'energies',
          label: "Energies",
        },
          {% endif %}
          {% if 'feature_id' in result_fields %}
        {
          id: 'feature',
          sasipediaId: 'features',
          label: "Features",
        },
          {% endif %}
          {% if 'feature_category_id' in result_fields %}
        {
          id: 'feature_category',
          sasipediaId: 'features',
          label: "Feature Categories",
        },
          {% endif %}
          {% if 'gear_id' in result_fields %}
        {
          id: 'gear',
          sasipediaId: 'gears',
          label: "Generic Gears",
        },
          {% endif %}
        ]
      });

      return dvConfigs;
    };


    var generateFishingResultConfigs = function(){
      var dvConfigs = generateDataViewConfigs({
        table: 'fishing_result',
        fields: [
          {
          id: 'a',
          label: 'Raw Swept Area',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
          format: '%.1H km<sup>2</sup>',
        },
        {% if not model_parameters.effort_model == 'nominal' -%}
        {
          id: 'value',
          label: 'Value',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:G',
        },
        {
          id: 'value_net',
          label: 'Cumulative Value',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:G',
        },
        {
          id: 'hours_fished',
          label: 'Hours Fished',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:G',
        },
        {
          id: 'hours_fished_net',
          label: 'Cumulative Hours Fished',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:G',
        },
        {% endif -%}
        ],
        facetFields: [
          {
          id: 'generic_gear',
          sasipediaId: 'gears',
          label: "Generic Gears",
          tableCol: 'generic_gear_id',
          keyTable: 'gear',
        },
        {
          id: 'all_gear',
          sasipediaId: 'gears',
          label: "All Gears",
          tableCol: 'gear_id',
          keyTable: 'gear',
        },
        ],
      });

      return dvConfigs;
    };

    GeoRefine.config.dataViewGroups = [
      {
      label: 'SASI Results',
      models: generateSasiResultConfigs(),
    },
    {
      label: 'Fishing Efforts',
      models: generateFishingResultConfigs(),
    },
    ];

    GeoRefine.config.projectInfo = {
      label: 'Info',
      infoLink: '{{PROJECT_STATIC_DIR}}/sasipedia/index.html',
    };
  };

  if (! GeoRefine){
    GeoRefine = {};
  }

  if (! GeoRefine.config){
    GeoRefine.config = {};
  }

  if (! GeoRefine.preInitializeHooks){
    GeoRefine.preInitializeHooks = [];
  }
  GeoRefine.preInitializeHooks.push({
    fn: setUpSasiConfig,
  });

}).call(this);
