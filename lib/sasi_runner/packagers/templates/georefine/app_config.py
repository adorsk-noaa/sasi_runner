# This object will contain the app config.
app_config = {}

# Quantity fields are used in facets and charts.
app_config['quantity_fields'] = {}

# Area field is special because it does not have a key expression.
area_quantity_field = {
    'id': 'cell_area_sum',
    'label': 'Cell Area',
    'info': 'Cell Area Info', #@TODO
    'value_type': 'numeric',
    'inner_query': {
        'SELECT': [{'ID': 'cell_id', 'EXPRESSION': '__result__cell_id'}],
        'GROUP_BY': [{'ID': 'cell_id'}],
    },
    'outer_query': {
        'SELECT': [{'ID': 'sum_cell_area', 'EXPRESSION': 'func.sum(__cell__area)'}],
        'FROM': [
            {
                'SOURCE': 'cell',
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__cell_id'
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__cell__id'
                            }
                        ],
                    ],
                ],
            }
        ]
    },
    'format': '%.1h m<sup>2</sup>'
}
app_config['quantity_fields']['cell_area:sum'] = area_quantity_field

# Add SASI swept area fields to quantity fields.
sasi_fields = [
    ['a', 'Unmodified Swept Area (A)', 0],
    ['y', 'Modified Swept Area (Y)'],
    ['x', 'Recovered Swept Area (X)'],
    ['z', 'Net Swept Area (Z)'],
    ['znet', 'Cumulative Net Swept Area (Znet)'],
]

sasi_quantity_fields = {}
for f in sasi_fields:
    field_id = "result_%s_sum" % f[0]
    sasi_quantity_field = {
        'id': field_id,
        'label': f[1],
        'info': 'da info {{PROJECT_STATIC_DIR}}',
        'value_type': 'numeric',
        'inner_query': {
            'SELECT': [
                {'ID': "%s_sum" % f[0], 'EXPRESSION': 'func.sum(__result__%s)' % f[0]},
            ],
        },
        'outer_query': {
            'SELECT': [{'ID': "%s_sum" % f[0], 'EXPRESSION': "__inner__%s_sum" % f[0]}],
        },
        'key_entity_expression': '__result__%s' % f[0],
        'format': '%.1h m<sup>2</sup>'
    }

    # Save to overall quantity fields, 
    # and sasi_quantity fields.
    app_config['quantity_fields'][field_id] = sasi_quantity_field
    sasi_quantity_fields[field_id] = sasi_quantity_field

app_config['filter_groups'] = [
    {'id': 'scenario'},
    {'id': 'data'}
]


app_config['facets'] = {
    "quantity_fields": app_config['quantity_fields'].values(),
    "definitions" : {
        'timestep': {
            'id': 'timestep',
            'facetDef': {
                'label': 'Timestep',
                'type': 'timeSlider',
                'KEY': {
                    'QUERY': {
                        'SELECT': [
                            {'ID': 't', 'EXPRESSION': '__time__id'},
                        ]
                    },
                    'KEY_ENTITY': {'ID': 't'}
                },
                'value_type': 'numeric',
                'choices': [],
                'primary_filter_groups': ['scenario'],
                'filter_entity': {'TYPE': 'ENTITY', 'ID': 't',
                                  'EXPRESSION': '__result__t'},
                'noClose': True
            },
        },
        'substrates': {
            'id': 'substrates',
            'facetDef': {
                'label': 'Substrates',
                'info': ('<p>See this link:'
                         ' <a href="'
                         '{{PROJECT_STATIC_DIR}}/sasipedia#substrates/index.html'
                         '" target="_blank">Substrates</a></p>'
                        ),
                'type': 'list',
                'KEY': {
                    'QUERY': {
                        'SELECT': [
                            {'ID': 'substrate_id', 'EXPRESSION': '__substrate__id'},
                            {'ID': 'substrate_name', 'EXPRESSION': '__substrate__label'},
                        ],
                    },
                    'KEY_ENTITY': {'ID': 'substrate_id'}, 
                    'LABEL_ENTITY': {'ID': 'substrate_name'},
                },
                'inner_query': {
                    'SELECT': [
                        {'ID': 'substrate_id', 'EXPRESSION':
                         '__result__substrate_id'},
                    ],
                    'GROUP_BY': [{'ID': 'substrate_id'}],
                },
                'outer_query': {
                    'SELECT': [
                        {'ID': 'substrate_name', 'EXPRESSION':
                         '__substrate__label'},
                        {'ID': 'substrate_id', 'EXPRESSION': '__substrate__id'}
                    ],
                    'FROM': [
                        {
                            'SOURCE': 'substrate',
                            'JOINS': [
                                [
                                    'inner', 
                                    [
                                        {
                                            'TYPE': 'ENTITY', 
                                            'EXPRESSION': '__inner__substrate_id'
                                        }, 
                                        '==', 
                                        {
                                            'TYPE': 'ENTITY', 
                                            'EXPRESSION':
                                            '__substrate__id'
                                        }
                                    ],
                                ],
                            ],
                        }
                    ],
                    'GROUP_BY': [
                        {'ID': 'substrate_name'},
                        {'ID': 'substrate_id'}
                    ],
                },
                'primary_filter_groups': ['data'],
                'base_filter_groups': ['scenario'],
                'filter_entity': {'TYPE': 'ENTITY', 'ID': 'substrate_id',
                                  'EXPRESSION': '__result__substrate_id'},
            },
        },
    }
}

# Add sasi quantity field facet definitions.
for qfield in sasi_quantity_fields.values():
    key_entity_id = 'facet%s_key_' % qfield['id']
    app_config['facets']['definitions'][qfield['id']] = {
        'id': qfield['id'],
        'facetDef': {
            'label': qfield['label'],
            'info': qfield['info'],
            'type': 'numeric',
            'inner_query': {
                'SELECT': [
                    {
                        'ID': key_entity_id,
                        'EXPRESSION': qfield['key_entity_expression'],
                        'AS_HISTOGRAM': True,
                        'ALL_VALUES': True,
                    },
                ]
            },
            'KEY': {
                'KEY_ENTITY': {'ID': key_entity_id}
            },
            'primary_filter_groups': ['data'],
            'base_filter_groups': ['scenario'],
            'filter_entity': {
                'TYPE': 'ENTITY', 
                'EXPRESSION': qfield['key_entity_expression'],
            },
            'range_auto': True
        },
    }

app_config['charts'] = {
    'primary_filter_groups': ['data'],
    'base_filter_groups': ['scenario'],
    'quantity_fields': app_config['quantity_fields'].values(),
    'category_fields': [
        {
            'id': 'substrates',
            'label': 'Substrates',
            'value_type': 'categorical',
            'KEY': {
                'KEY_ENTITY': {
                    'ID': '_cat_substrate_id', 
                    'EXPRESSION': '__result__substrate__id',
                    'ALL_VALUES': True
                },
                'LABEL_ENTITY': {'ID': 'substrate_name', 
                                 'EXPRESSION': '__result__substrate__label'},
            },
        },
    ],
}

# Add sasi quantity field histograms to category fields.
for qfield in sasi_quantity_fields.values():
    app_config['charts']['category_fields'].append({
        'id': qfield['id'],
        'label': qfield['label'],
        'value_type': 'numeric',
        'KEY': {
            'KEY_ENTITY': {
                'ID': '_cat_%s' % qfield['id'], 
                'EXPRESSION': qfield['key_entity_expression'],
                'AS_HISTOGRAM': True,
                'ALL_VALUES': True
            },
        },
    })

app_config['data_layers'] = []
for f in sasi_fields:
    data_layer = {
        "id": f[0],
        "label": "%s (density)" % f[1],
        "info": "info test",
        "source": "georefine_data_layer",
        "layer_type": 'WMS',
        "layer_category": 'data',
        "options": {},
        "params": {
            "transparent": True
        },
        "inner_query": {
            'SELECT': [
                {
                    'ID': "%s_data" % f[0], 
                    'EXPRESSION': "func.sum(__result__%s/__result__cell__area)" % f[0]
                },
            ],
            'GROUP_BY': [
                {
                    'ID': "%s_cell_id" % f[0], 
                    'EXPRESSION': '__result__cell__id'
                },
                {
                    'ID': "%s_cell_geom" % f[0], 
                    'EXPRESSION': '__result__cell__geom'
                }
            ],
        },
        "outer_query": {
            'SELECT': [
                {
                    'ID': "%s_geom_id" % f[0], 
                    'EXPRESSION': "__inner__%s_cell_id" % f[0]
                },
                {
                    'ID': "%s_geom" % f[0], 
                    'EXPRESSION': "__inner__%s_cell_geom" % f[0]
                },
                {
                    'ID': "%s_data" % f[0], 
                    'EXPRESSION': "__inner__%s_data" % f[0]
                },
            ]
        },
        "geom_id_entity": {'ID': "%s_geom_id" % f[0]},
        "geom_entity": {'ID': "%s_geom" % f[0]},
        "data_entity": {
            'ID': "%s_data" % f[0],
            'min': 0, # @TODO: SET SMART DEFAULTS BASED ON DATA.
            'max': 1, # @TODO: SET SMART DEFAULTS BASED ON DATA.
        },
    "disabled": True 
    }
    app_config['data_layers'].append(data_layer)

"""
app_config['maps'] = {
    "primary_filter_groups": ['data'],
    "base_filter_groups" : ['scenario'],
    "max_extent" : {=map_parameters.max_extent=},
    "graticule_intervals": {=map_parameters.graticule_intervals=},
    "resolutions": {=map_parameters.resolutions=},
    "default_layer_options" : {
        "transitionEffect": 'resize'
    },
    "default_layer_attributes": {
        "reorderable": True,
        "disabled": True,
    },

    "data_layers": app_config['data_layers'],
    {% for layer_category in ['base', 'overlay'] %}
    "{= layer_category =}_layers": [
        {% for layer in map_layers[layer_category] %}
        {
            {# direct attrs #}
            {% for attr, value in layer.attrs.items() %}
            '{= attr =}':{= value =},
            {% endfor %}
            {# wms parameters #}
            'params': {
                {% for attr, value in layer.wms_params.items() %}
                '{= attr =}':{= value =},
                {% endfor %}
            },
            {# options #}
            'options': {
                {% for attr, value in layer.options.items() %}
                '{= attr =}':{= value =},
                {% endfor %}
            },
        },
        {% endfor %}
    ],
    {% endfor %}
}
"""

app_config['defaultInitialState'] = {
    'filterGroups': app_config['filter_groups'],
    'facetsEditor': {
        'quantity_fields': app_config['quantity_fields'],
        'summary_bar': {
            'primary_filter_groups': ['data'],
            'base_filter_groups': ['scenario']
        },
        'predefined_facets': app_config['facets']['definitions'].values()
    },

    'initialActionQueue': {
        "async": False,
        "actions": [
            # Set quantity field.
            {
                "type":"action",
                "handler":"facets_facetsEditorSetQField",
                "opts":{
                    "id":"cell_area_sum"
                }
            },
            # Timestep facet.
            {
                "type":"actionQueue",
                "async":False,
                "actions":[

                    {
                        "type":"action",
                        "handler":"facets_addFacet",
                        "opts":{
                            "fromDefinition":True,
                            "category":"base",
                            "defId":"timestep",
                            "facetId":"tstep"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_initializeFacet",
                        "opts":{
                            "category":"base",
                            "id":"tstep"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_connectFacet",
                        "opts":{
                            "category":"base",
                            "id":"tstep"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_getData",
                        "opts":{
                            "category":"base",
                            "id":"tstep"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_setSelection",
                        "opts":{
                            "category":"base",
                            "id":"tstep",
                            "index":1
                        }
                    }
                ]
            },

            # Summary bar.
            {
                "type":"actionQueue",
                "async":False,
                "actions":[
                    {
                        "type":"action",
                        "handler":"summaryBar_initialize"
                    },
                    {
                        "type":"action",
                        "handler":"summaryBar_connect"
                    },
                    {
                        "type":"action",
                        "handler":"summaryBar_getData"
                    }
                ]
            },

            # Substrates facet.
            {
                "type":"actionQueue",
                "async":False,
                "actions":[
                    {
                        "type":"action",
                        "handler":"facets_addFacet",
                        "opts":{
                            "fromDefinition":True,
                            "category":"primary",
                            "defId":"substrates",
                            "facetId":"initSubstrates"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_initializeFacet",
                        "opts":{
                            "category":"primary",
                            "id":"initSubstrates"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_connectFacet",
                        "opts":{
                            "category":"primary",
                            "id":"initSubstrates"
                        }
                    },
                    {
                        "type":"action",
                        "handler":"facets_getData",
                        "opts":{
                            "category":"primary",
                            "id":"initSubstrates"
                        }
                    }
                ]
            },

            # Data Views.
            #{
                #"type":"actionQueue",
                #"async":True,
                #"actions":[

                    ## Chart view.
                    #{
                        #"type":"actionQueue",
                        #"async":False,
                        #"actions":[
                            #{
                                #"type":"action",
                                #"handler":"dataViews_createFloatingDataView",
                                #"opts":{
                                    #"id":"initialChart",
                                    #"dataView":{
                                        #"type":"chart"
                                    #}
                                #}
                            #},
                            #{
                                #"type":"action",
                                #"handler":"dataViews_selectChartFields",
                                #"opts":{
                                    #"id":"initialChart",
                                    #"categoryField":{
                                        #"id":"substrates"
                                    #},
                                    #"quantityField":{
                                        #"id":"result_cell_area_sum"
                                    #}
                                #}
                            #}
                        #]
                    #},

                    ## @TODO: Add Map view here.
                #]
            #}
        ]
    }
}
