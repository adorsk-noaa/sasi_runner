(function(){
  if (! GeoRefine){
    GeoRefine = {};
  }

  if (! GeoRefine.config){
    GeoRefine.config = {};
  }

  if (! GeoRefine.preInitializeHooks){
    GeoRefine.preInitializeHooks = [];
  }

  var setUpSasiConfig = function($, Backbone, _, _s){

    var overlayLayers = {
      graticule: new Backbone.Model({
        layer_type:"Graticule",
        label:"Lat/Lon Grid",
        disabled: true,
      })
    };

    var defaultLayerOptions = {
      transitionEffect:"resize",
      tileSize: {w:1024, h:1024},
      buffer: 0
    };
    {% if map_config.defaultLayerOptions %}
    $.extend(true, defaultLayerOptions, {= map_config.defaultLayerOptions =});
    {% endif %}

    var defaultLayerAttributes = {
      disabled: true,
    };
    {% if map_config.defaultLayerAttributes%}
    $.extend(true, defaultLayerOptions, {= map_config.defaultLayerAttributes =});
    {% endif %}

    var defaultMapOptions = {
      maxExtent: [-180, -90, 180, 90],
      extent: [-180, 90, -180, 90],
      resolutions:[0.025,0.0125,0.00625,0.003125,0.0015625,0.00078125],
      options: {
        allOverlays: true
      },
    };
    {% if map_config.defaultMapOptions%}
    $.extend(true, defaultMapOptions, {= map_config.defaultMapOptions =});
    {% endif %}
    var defaultMap = new Backbone.Model(defaultMapOptions);

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
      var idId = field.id + '_id';
      var labelId = field.id + '_label';
      var tableColExpression = '__' + opts.table + '__' + idId;
      var idColExpression = '__' + field.id + '__id';
      var labelColExpression = '__' + field.id + '__label';
      var infoLink = "{{PROJECT_STATIC_DIR}}/sasipedia/index.html#" + field.sasipediaId + '/index.html' || field.infoLink;
      var infoContent = _s.sprintf(
        '%s Click <a href="%s" target="_blank">here</a> for more information.',
        field.infoText, infoLink);

        $.extend(true, modelOpts, {
          info: infoContent,
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
              SOURCE: field.id,
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

    var generateDataLayerModel = function(opts){
      var field = opts.field;
      var densityId = field.col + '_density';
      var propertyMappings = [
        {source: densityId, target: densityId, default: 0.0},
      ];

      var scaleOpts = {};
      if (field.scale){
        scaleOpts.scale_type = field.scale_type;
        if (scaleOpts.type == 'sequential'){
          scaleOpts.vmin = 0;
          scaleOpts.vmaxAuto = true;
        }
        else if (scaleOpts.type == 'diverging'){
          scaleOpts.vmid = field.scale_mid;
          scaleOpts.vrAuto = true;
        }
      };

      var modelOpts = {};
      $.extend(true, modelOpts, scaleOpts, {
        id: field.id,
        colormapId: field.colormapId,
        dataProp: densityId,
        layer_type: 'Vector',
        layer_category: 'data',
        source: 'georefine_data',
        label: field.label + ', per unit cell area',
        disabled: false,
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
          strokeWidth: 0, 
        })
        ])
      });

      $.extend(true, modelOpts, field);

      return new Backbone.Model(modelOpts);
    };

    var generateInitialActions = function(){
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
            index: 1,
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

      var dataLayers = {};
      _.each(opts.fields, function(field){
        dataLayers[field.id] = generateDataLayerModel({
          field: field,
          table: opts.table,
        });
      });

      var initialActions = generateInitialActions();

      var dvConfigs = [];
      _.each(opts.fields, function(field){
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
            map: defaultMap.clone(),
            base_layers: new Backbone.Collection(
              [baseLayers['world']]
            ) ,
            overlay_layers: new Backbone.Collection(
              [
                dataLayers[field.id],
                overlayLayers.graticule,
            ])
          }),
          initialActions: initialActions,
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
          label: 'A label',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Rd',
        },
        {
          id: 'y',
          label: 'Y label',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
        },
        {
          id: 'x',
          label: 'X label',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Br',
        },
        {
          id: 'z',
          label: 'Z label',
          scale_type: 'diverging',
          scale_mid: 0,
          colormapId: 'ColorBrewer:PiG',
        },
        {
          id: 'znet',
          label: 'Znet label',
          scale_type: 'diverging',
          scale_mid: 0,
          colormapId: 'ColorBrewer:Rd:Bu',
        },
        ],
        facetFields: [
          {
          id: 'substrate',
          sasipediaId: 'substrates',
          infoText: 'substrates info',
          label: "Substrates",
        },
        {
          id: 'energy',
          sasipediaId: 'energies',
          infoText: 'energy info',
          label: "Energies",
        },
        {
          id: 'feature',
          sasipediaId: 'features',
          infoText: 'feature info',
          label: "Features",
        },
        {
          id: 'feature_category',
          sasipediaId: 'feature_categories',
          infoText: 'feature category info',
          label: "Feature Categories",
        },
        {
          id: 'gear',
          sasipediaId: 'gears',
          infoText: 'gear info',
          label: "Gear",
        },
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
          colormapId: 'ColorBrewer:Rd',
        },
        {
          id: 'value',
          label: 'Value',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
        },
        {
          id: 'value_net',
          label: 'Cumulative Value',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Pi',
        },
        {
          id: 'hours_fished_net',
          label: 'Cumulative Hours Fished',
          scale_type: 'sequential',
          colormapId: 'ColorBrewer:Br',
        },
        ],
        // @TODO: Add specific gear facet too?
        facetFields: [
          {
          id: 'generic_gear',
          sasipediaId: 'gears',
          infoText: 'generic gear info',
          label: "Generic Gear",
          KEY: {
            QUERY: {
              WHERE: [
                [{
                TYPE: 'ENTITY',
                EXPRESSION: '__gear__is_generic',
              }, '==', true, ]
              ]
            }
          },
        },
        {
          id: 'specific_gear',
          sasipediaId: 'gears',
          infoText: 'specific gear info',
          label: "Specific Gear",
          KEY: {
            QUERY: {
              WHERE: [
                [{
                TYPE: 'ENTITY',
                EXPRESSION: '__gear__is_generic',
              }, '!=', true, ]
              ]
            }
          },
        },
        ],
      });

      return dvConfigs;
    };

    GeoRefine.config.dataViewGroups = [
      {
      label: 'SASI Results',
      models: generateResultsConfigs(),
    },
    {
      label: 'Fishing Efforts',
      models: generateFishingEffortsConfigs(),
    },
    ];

    GeoRefine.config.projectInfo = {
      label: 'Info',
      infoLink: '{{PROJECT_STATIC_DIR}}/sasipedia/index.html',
    };
  };

}).call(this);
