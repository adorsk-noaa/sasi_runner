# This object will contain the app config.
app_config = {}

#
# SASI swept area fields.
#
sasi_fields = [
    ['a', 'Unmodified Swept Area (A)', 0],
    ['y', 'Modified Swept Area (Y)'],
    ['x', 'Recovered Swept Area (X)'],
    ['z', 'Net Swept Area (Z)'],
    ['znet', 'Cumulative Net Swept Area (Znet)'],
]

#
# Quantity Fields.
# Quantity fields are used in facets and charts.
# They represent y-values in a chart, or a count in a facet.
#
quantity_fields = {}

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
quantity_fields['cell_area_sum'] = area_quantity_field

# Generate quantity fields from sasi fields.
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
    quantity_fields[field_id] = sasi_quantity_field
    sasi_quantity_fields[field_id] = sasi_quantity_field

# 
# Category Fields.
# Category fields represent x-values in a chart, or categories in a facet.
# They describe key/label entities, and query alterations.
#
category_fields = {}

# Substrates category.
category_fields['substrates'] = {
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
}

# Gears category.
category_fields['gears'] = {
    'KEY': {
        'QUERY': {
            'SELECT': [
                {'ID': 'gear_id', 'EXPRESSION': '__gear__id'},
                {'ID': 'gear_name', 'EXPRESSION': '__gear__label'},
            ],
        },
        'KEY_ENTITY': {'ID': 'gear_id'}, 
        'LABEL_ENTITY': {'ID': 'gear_name'},
    },
    'inner_query': {
        'SELECT': [
            {'ID': 'gear_id', 'EXPRESSION':
             '__result__gear_id'},
        ],
        'GROUP_BY': [{'ID': 'gear_id'}],
    },
    'outer_query': {
        'SELECT': [
            {'ID': 'gear_name', 'EXPRESSION':
             '__gear__label'},
            {'ID': 'gear_id', 'EXPRESSION': '__gear__id'}
        ],
        'FROM': [
            {
                'SOURCE': 'gear',
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__gear_id'
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__gear__id'
                            }
                        ],
                    ],
                ],
            }
        ],
        'GROUP_BY': [
            {'ID': 'gear_name'},
            {'ID': 'gear_id'}
        ],
    },
}

# Energies category.
category_fields['energies'] = {
    'KEY': {
        'QUERY': {
            'SELECT': [
                {'ID': 'energy_id', 'EXPRESSION': '__energy__id'},
                {'ID': 'energy_name', 'EXPRESSION': '__energy__label'},
            ],
        },
        'KEY_ENTITY': {'ID': 'energy_id'}, 
        'LABEL_ENTITY': {'ID': 'energy_name'},
    },
    'inner_query': {
        'SELECT': [
            {'ID': 'energy_id', 'EXPRESSION':
             '__result__energy_id'},
        ],
        'GROUP_BY': [{'ID': 'energy_id'}],
    },
    'outer_query': {
        'SELECT': [
            {'ID': 'energy_name', 'EXPRESSION':
             '__energy__label'},
            {'ID': 'energy_id', 'EXPRESSION': '__energy__id'}
        ],
        'FROM': [
            {
                'SOURCE': 'energy',
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__energy_id'
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__energy__id'
                            }
                        ],
                    ],
                ],
            }
        ],
        'GROUP_BY': [
            {'ID': 'energy_name'},
            {'ID': 'energy_id'}
        ],
    },
}

# Features category
category_fields['features'] = {
    'KEY': {
        'QUERY': {
            'SELECT': [
                {'ID': 'feature_id', 'EXPRESSION': '__feature__id'},
                {'ID': 'feature_name', 'EXPRESSION': '__feature__label'},
            ],
        },
        'KEY_ENTITY': {'ID': 'feature_id'}, 
        'LABEL_ENTITY': {'ID': 'feature_name'},
    },
    'inner_query': {
        'SELECT': [
            {'ID': 'feature_id', 'EXPRESSION':
             '__result__feature_id'},
        ],
        'GROUP_BY': [{'ID': 'feature_id'}],
    },
    'outer_query': {
        'SELECT': [
            {'ID': 'feature_name', 'EXPRESSION':
             '__feature__label'},
            {'ID': 'feature_id', 'EXPRESSION': '__feature__id'}
        ],
        'FROM': [
            {
                'SOURCE': 'feature',
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__feature_id'
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__feature__id'
                            }
                        ],
                    ],
                ],
            }
        ],
        'GROUP_BY': [
            {'ID': 'feature_name'},
            {'ID': 'feature_id'}
        ],
    },
}

# Feature Category category
category_fields['feature_category'] = {
    'KEY': {
        'QUERY': {
            'SELECT': [
                {'ID': 'feature_category_id', 'EXPRESSION': '__feature_category__id'},
                {'ID': 'feature_category_name', 'EXPRESSION': '__feature_category__label'},
            ],
        },
        'KEY_ENTITY': {'ID': 'feature_category_id'}, 
        'LABEL_ENTITY': {'ID': 'feature_category_name'},
    },
    'inner_query': {
        'SELECT': [
            {'ID': 'feature_category_id', 'EXPRESSION':
             '__result__feature_category_id'},
        ],
        'GROUP_BY': [{'ID': 'feature_category_id'}],
    },
    'outer_query': {
        'SELECT': [
            {'ID': 'feature_category_name', 'EXPRESSION':
             '__feature_category__label'},
            {'ID': 'feature_category_id', 'EXPRESSION': '__feature_category__id'}
        ],
        'FROM': [
            {
                'SOURCE': 'feature_category',
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__feature_category_id'
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__feature_category__id'
                            }
                        ],
                    ],
                ],
            }
        ],
        'GROUP_BY': [
            {'ID': 'feature_category_name'},
            {'ID': 'feature_category_id'}
        ],
    },
}

# SASI histgram category fields.
# These fields are histograms of 
# SASI quantity fields.
for qfield in sasi_quantity_fields.values():
    key_entity_id = 'facet%s_key_' % qfield['id']
    key_entity = {
        'ID': key_entity_id,
        'EXPRESSION': qfield['key_entity_expression'],
        'AS_HISTOGRAM': True,
        'ALL_VALUES': True,
    }
    category_fields[qfield['id']] = {
        'KEY': {
            'KEY_ENTITY': key_entity
        },
        'inner_query': {
            'SELECT': [key_entity],
            'GROUP_BY': [key_entity],
        },
        'outer_query': {
            'SELECT': [{
                'ID': key_entity['ID'], 
                'EXPRESSION': "__inner__%s" % key_entity['ID']
            }],
            'GROUP_BY': [{'ID': key_entity['ID']}],
        },
    }
        

# 
# Filter Groups.
#
filter_groups = [
    {'id': 'scenario'},
    {'id': 'data'}
]
app_config['filter_groups'] = filter_groups


#
# Facets.
#
facets = {}
facets['quantity_fields'] = quantity_fields
facets['definitions'] = {}

# Timestep facet.
facets['definitions']['timestep'] = {
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
}

# Substrates facet.
facets['definitions']['substrates'] =  {
    'id': 'substrates',
    'facetDef': {
        'label': 'Substrates',
        'info': ('<p>See this link:'
                 ' <a href="'
                 '{{PROJECT_STATIC_DIR}}/sasipedia#substrates/index.html'
                 '" target="_blank">Substrates</a></p>'
                ),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 'substrate_id',
                          'EXPRESSION': '__result__substrate_id'},
    },
}
facets['definitions']['substrates']['facetDef'].update(
    category_fields['substrates'])

# Gears facet.
facets['definitions']['gears'] =  {
    'id': 'gears',
    'facetDef': {
        'label': 'Gears',
        'info': ('<p>See this link:'
                 ' <a href="'
                 '{{PROJECT_STATIC_DIR}}/sasipedia#gears/index.html'
                 '" target="_blank">Gears</a></p>'
                ),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 'gear_id',
                          'EXPRESSION': '__result__gear_id'},
    },
}
facets['definitions']['gears']['facetDef'].update(
    category_fields['gears'])

# Energy facet.
facets['definitions']['energies'] =  {
    'id': 'energies',
    'facetDef': {
        'label': 'Energies',
        'info': ('<p>See this link:'
                 ' <a href="'
                 '{{PROJECT_STATIC_DIR}}/sasipedia#energies/index.html'
                 '" target="_blank">Energies</a></p>'
                ),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 'energy_id',
                          'EXPRESSION': '__result__energy_id'},
    },
}
facets['definitions']['energies']['facetDef'].update(
    category_fields['energies'])

# Features facet.
facets['definitions']['features'] =  {
    'id': 'features',
    'facetDef': {
        'label': 'Features',
        'info': ('<p>See this link:'
                 ' <a href="'
                 '{{PROJECT_STATIC_DIR}}/sasipedia#features/index.html'
                 '" target="_blank">Features</a></p>'
                ),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 'feature_id',
                          'EXPRESSION': '__result__feature_id'},
    },
}
facets['definitions']['features']['facetDef'].update(
    category_fields['features'])

# Feature Category facet.
facets['definitions']['feature_category'] =  {
    'id': 'feature_category',
    'facetDef': {
        'label': 'Feature Categories',
        'info': ('<p>See this link:'
                 ' <a href="'
                 '{{PROJECT_STATIC_DIR}}/sasipedia#feature_categories/index.html'
                 '" target="_blank">Feature Categories</a></p>'
                ),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 'feature_category_id',
                          'EXPRESSION': '__result__feature_category_id'},
    },
}
facets['definitions']['feature_category']['facetDef'].update(
    category_fields['feature_category'])

# SASI quantity field facets.
for qfield in sasi_quantity_fields.values():
    facets['definitions'][qfield['id']] = {
        'id': qfield['id'],
        'facetDef': {
            'label': qfield['label'],
            'info': qfield['info'],
            'type': 'numeric',
            'primary_filter_groups': ['data'],
            'base_filter_groups': ['scenario'],
            'filter_entity': {
                'TYPE': 'ENTITY', 
                'EXPRESSION': qfield['key_entity_expression'],
            },
            'range_auto': True
        },
    }
    facets['definitions'][qfield['id']]['facetDef'].update(
        category_fields[qfield['id']]
    )
app_config['facets'] = facets


#
# Charts.
#
charts = {
    'primary_filter_groups': ['data'],
    'base_filter_groups': ['scenario'],
    'quantity_fields': quantity_fields.values(),
    'category_fields': []
}

# Substrates category.
charts['category_fields'].append(
    dict({
        'id': 'substrates',
        'label': 'Substrates',
        'value_type': 'categorical',
    }.items() + category_fields['substrates'].items())
)

# SASI field categories.
for qfield in sasi_quantity_fields.values():
    charts['category_fields'].append(
        dict({
            'id': qfield['id'],
            'label': qfield['label'],
            'value_type': 'numeric',
        }.items() + category_fields[qfield['id']].items())
    )
app_config['charts'] = charts


#
# Maps.
#

data_layers = []
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
                    'EXPRESSION': "func.sum(__result__%s)" % f[0]
                },
            ],
            'GROUP_BY': [
                {
                    'ID': "cell_id",
                    'EXPRESSION': '__result__cell_id'
                },
            ],
        },
        "outer_query": {
            'SELECT': [
                {
                    'ID': "%s_geom_id" % f[0], 
                    'EXPRESSION': "__cell__id",
                },
                {
                    'ID': "%s_geom" % f[0], 
                    'EXPRESSION': "__cell__geom",
                },
                {
                    'ID': "%s_data" % f[0], 
                    'EXPRESSION': "__inner__%s_data / __cell__area" % f[0]
                },
            ],
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
                                    'EXPRESSION': '__cell__id'
                                }
                            ],
                        ],
                    ],
                }
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
    #"max_extent": [-180,-90, 180, 90],
    "graticule_intervals": {=map_parameters.graticule_intervals=},
    #"graticule_intervals": [2],
    "resolutions": {=map_parameters.resolutions=},
    #"resolutions": [0.025, 0.0125, 0.00625, 0.003125, 0.0015625, 0.00078125],
    "default_layer_options" : {
        "transitionEffect": 'resize'
    },
    "default_layer_attributes": {
        "reorderable": True,
        "disabled": True,
    },

    "data_layers": data_layers,
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
app_config['maps'] = maps

app_config['defaultInitialState'] = {
    'filterGroups': app_config['filter_groups'],
    'facetsEditor': {
        'quantity_fields': quantity_fields,
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
            {
                "type":"actionQueue",
                "async":True,
                "actions": [

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
                                        "id":"cell_area_sum"
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
