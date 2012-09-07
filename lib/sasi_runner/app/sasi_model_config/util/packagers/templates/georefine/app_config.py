sasipedia_base_url = "/georefine/static/sasipedia"

# Quantity fields are used in facets and charts.
quantity_fields = {
    'results.cell.area:sum': { 
        'id': 'results.cell.area:sum',
        'label': 'Cell Area',
        'info': 'Cell Area Info', #@TODO
        'value_type': 'numeric',
        'inner_query': {
            'SELECT': [{'ID': 'cell_area', 'EXPRESSION': '{{results.cell.area}}/1000000.0'}],
            'GROUP_BY': [
                '{{results.cell.id}}',
                {'ID': 'cell_area'}
            ],
        },
        'outer_query': {
            'SELECT': [{'ID': 'sum_cell_area', 'EXPRESSION': 'func.sum({{inner.cell_area}})'}],
        },
        'format': '%.1h km<sup>2</sup>'
    },
}

# Add SASI swept area fields to quantity fields.
sasi_fields = [
    ['a', 'Unmodified Swept Area (A)', 0],
    ['y', 'Modified Swept Area (Y)'],
    ['x', 'Recovered Swept Area (X)'],
    ['z', 'Net Swept Area (Z)'],
    ['znet', 'Cumulative Net Swept Area (Znet)'],
]

for f in sasi_fields:
    field_id = "results.%s:sum" % f[0]
    quantity_fields[field_id] = {
        'id': field_id,
        'label': f[1],
        'info': 'da info', #@TODO
        'value_type': 'numeric',
        'inner_query': {
            'GROUP_BY': [
                {'ID': f[0], 'EXPRESSION': "{{results.%s}}/1000000.0" % f[0]},
                '{{results.id}}'
            ],
        },
        'outer_query': {
            'SELECT': [{'ID': "%s_sum" % f[0], 'EXPRESSION': "func.sum({{inner.%s}})" % f[0]}],
        },
        'format': '%.1h km<sup>2</sup>'
    }

filter_groups = [
    {'id': 'scenario'},
    {'id': 'data'}
]


facets = {
    "quantity_fields": quantity_fields.values(),
    "definitions" : {
        'timestep': {
            'id': 'timestep',
            'facetDef': {
                'label': 'Timestep',
                'type': 'timeSlider',
                'KEY': {
                    'KEY_ENTITY': {'ID': 'result_t', 'EXPRESSION': '{{results.t}}'},
                    'LABEL_ENTITY': {'ID': 'result_t'},
                },
                'value_type': 'numeric',
                'choices': [],
                'primary_filter_groups': ['scenario'],
                'filter_entity': '{{results.t}}',
                'noClose': True
            },
        },
        'substrates': {
            'id': 'substrates',
            'facetDef': {
                'label': 'Substrates',
                'info': 'Info test',
                'type': 'list',
                'KEY': {
                    'KEY_ENTITY': {'ID': 'substrate_id', 'EXPRESSION':
                                   '{{results.substrate.id}}'},
                    'LABEL_ENTITY': {'ID': 'substrate_name', 'EXPRESSION':
                                     '{{results.substrate.label}}'},
                },
                'primary_filter_groups': ['data'],
                'base_filter_groups': ['scenario'],
                'filter_entity': '{{results.substrate.id}}'
            },
        },
    }
}

# Add quantity field facet definitions.
for qfield in quantity_fields.values():
    facets['definitions'][qfield['id']] = {
        'id': qfield['id'],
        'facetDef': {
            'label': qfield['label'],
            'info': qfield['info'],
            'type': 'numeric',
            'KEY': {
                'KEY_ENTITY': {
                    'ID': 'facet%s_%s' % (qfield['id'], qfield['id']), 
                    'EXPRESSION': '{{results.%s}}' % qfield['id'],
                    'AS_HISTOGRAM': True,
                    'ALL_VALUES': True
                },
            },
            'primary_filter_groups': ['data'],
            'base_filter_groups': ['scenario'],
            'filter_entity': '{{results.%s}}' % qfield['id'],
            'range_auto': True
        },
    }

charts = {
    'primary_filter_groups': ['data'],
    'base_filter_groups': ['scenario'],
    'quantity_fields': quantity_fields.values(),
    'category_fields': [
        {
            'id': 'substrates',
            'label': 'Substrates',
            'value_type': 'categorical',
            'KEY': {
                'KEY_ENTITY': {
                    'ID': '_cat_substrate_id', 
                    'EXPRESSION': '{{results.substrate.id}}',
                    'ALL_VALUES': True
                },
                'LABEL_ENTITY': {'ID': 'substrate_name', 'EXPRESSION': '{{results.substrate.name}}'},
            },
        },
    ],
}

# Add quantity field histograms to category fields.
for qfield in quantity_fields.values():
    charts['category_fields'].append({
        'id': qfield['id'],
        'label': qfield['label'],
        'value_type': 'numeric',
        'KEY': {
            'KEY_ENTITY': {
                'ID': '_cat_%s' % qfield['id'], 
                'EXPRESSION': '{{results.%s}}' % qfield['id'],
                'AS_HISTOGRAM': True,
                'ALL_VALUES': True
            },
        },
    })

data_layers = []
for f in sasi_fields:
    data_layer = {
        "id": f[0],
        "name": "%s (density)" % f[1],
        "info": "info test",
        "source": "local_getmap",
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
                    'EXPRESSION': "func.sum({{results.%s}}/{{results.cell.area}})" % f[0]
                },
            ],
            'GROUP_BY': [
                {
                    'ID': "%s_cell_id" % f[0], 
                    'EXPRESSION': '{{results.cell.id}}'
                },
                {
                    'ID': "%s_cell_geom" % f[0], 
                    'EXPRESSION': 'RawColumn({{results.cell.geom}})'
                }
            ],
        },
        "outer_query": {
            'SELECT': [
                {
                    'ID': "%s_geom_id" % f[0], 
                    'EXPRESSION': "{{inner.%s_cell_id}}" % f[0]
                },
                {
                    'ID': "%s_geom" % f[0], 
                    'EXPRESSION': "RawColumn({{inner.%s_cell_geom}})" % f[0]
                },
                {
                    'ID': "%s_data" % f[0], 
                    'EXPRESSION': "{{inner.%s_data}}" % f[0]
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
    data_layers.append(data_layer)

maps = {
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

    "data_layers": data_layers,
    "base_layers": [
        # @TODO: SET THIS FROM DATA.
    ],

    "overlay_layers": [
        # @TODO: SET THIS FROM DATA.
    ]
}

defaultInitialState = {
    'filterGroups': filter_groups,
    'facetsEditor': {
        'quantity_fields': quantity_fields,
        'summary_bar': {
            'primary_filter_groups': ['data'],
            'base_filter_groups': ['scenario']
        },
        'predefined_facets': facets['definitions'].values()
    },

    'initialActionQueue': {
        "async": False,
        "actions": [
            # Set quantity field.
            {
                "type":"action",
                "handler":"facets_facetsEditorSetQField",
                "opts":{
                    "id":"result.x:sum"
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
            {
                "type":"actionQueue",
                "async":True,
                "actions":[

                    # Chart view.
                    {
                        "type":"actionQueue",
                        "async":False,
                        "actions":[
                            {
                                "type":"action",
                                "handler":"dataViews_createFloatingDataView",
                                "opts":{
                                    "id":"initialChart",
                                    "dataView":{
                                        "type":"chart"
                                    }
                                }
                            },
                            {
                                "type":"action",
                                "handler":"dataViews_selectChartFields",
                                "opts":{
                                    "id":"initialChart",
                                    "categoryField":{
                                        "id":"substrates"
                                    },
                                    "quantityField":{
                                        "id":"result.cell.area:sum"
                                    }
                                }
                            }
                        ]
                    },

                    # @TODO: Add Map view here.
                ]
            }
        ]
    }
}
