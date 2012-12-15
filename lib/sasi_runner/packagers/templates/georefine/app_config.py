# This object will contain the app config.
app_config = {}

INFO_LINK_PREFIX = '{{PROJECT_STATIC_DIR}}/sasipedia'

sasi_numeric_fields = {
    'a': {
        'label': 'Unmodified Swept Area (A)',
    },
    'y': {
        'label': 'Modified Swept Area (Y)',
    },
    'x': {
        'label': 'Recovered Swept Area (X)',
    },
    'z': {
        'label': 'Net Swept Area (Z)',
    },
    'znet': {
        'label':'Cumulative Net Swept Area (Znet)',
    },
}
# Decorate numeric fields to set defaults.
for field_id, field in sasi_numeric_fields.items():
    field.setdefault('key_entity_expression',  '__result__%s' % field_id)
    field.setdefault('format',  '%.1h m<sup>2</sup>')

sasi_categorical_fields = {
    'substrate': {},
    'gear': {},
    'energy': {
        'label': 'Energies', 
        'info_link': INFO_LINK_PREFIX + '#energies/index.html' 
    },
    'feature': {},
    'feature_category': {
        'label': 'Feature Categories',
        'info_link': INFO_LINK_PREFIX + '#feature_categories/index.html'
    }
}

# Decorate categorical fields to set defaults.
for field_id, field in sasi_categorical_fields.items():
    field.setdefault('label', field_id.capitalize() + 's')
    field.setdefault('info_link', 
                     INFO_LINK_PREFIX + '#%ss/index.html' % field_id)

    key = field.setdefault('KEY', {})
    key.setdefault('QUERY', {
        'SELECT': [
            {
                'ID': '%s_id' % field_id,
                'EXPRESSION': '__%s__id' % field_id,
            },
            {
                'ID': '%s_label' % field_id,
                'EXPRESSION': '__%s__label' % field_id,
            },
        ]
    })
    key.setdefault('KEY_ENTITY', {
        'ID': '%s_id' % field_id,
        'EXPRESSION': '__result__%s_id' % field_id,
    })
    key.setdefault('LABEL_ENTITY',{
        'ID': '%s_label' % field_id,
    })

    field.setdefault('inner_query', {
        'SELECT': [key['KEY_ENTITY']],
        'GROUP_BY': [key['KEY_ENTITY']],
    })

    field.setdefault('outer_query', {
        'SELECT': key['QUERY']['SELECT'],
        'FROM': [
            {
                'SOURCE': '%s' % field_id,
                'JOINS': [
                    [
                        'inner', 
                        [
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION': '__inner__%s_id' % field_id,
                            }, 
                            '==', 
                            {
                                'TYPE': 'ENTITY', 
                                'EXPRESSION':
                                '__%s__id' % field_id,
                            }
                        ],
                    ],
                ],
            }
        ],
        'GROUP_BY': [
            {'ID': '%s_label' % field_id},
            {'ID': '%s_id' % field_id},
        ],
    })

    field.setdefault('filter_entity', {
        'TYPE': 'ENTITY', 
        'ID': field_id,
        'EXPRESSION': '__result__%s_id' % field_id,
    })

#
# Quantity Field Definitions.
# Quantity fields are used in facets and charts.
# They represent y-values in a chart, or a count in a facet.
#
quantity_fields = {}

# Generate quantity fields from sasi numeric fields.
sasi_quantity_fields = {}
for field_id, field in sasi_numeric_fields.items():
    # Sums.
    qfield_id = "result_%s_sum" % field_id
    qfield = {
        'id': qfield_id,
        'label': field['label'],
        'info': field.get('info'),
        'value_type': 'numeric',
        'inner_query': {
            'SELECT': [
                {
                    'ID': "%s_sum" % field_id, 
                    'EXPRESSION': 'func.sum(__result__%s)' % field_id,
                },
            ],
        },
        'outer_query': {
            'SELECT': [
                {
                    'ID': "%s_sum" % field_id, 
                    'EXPRESSION': "__inner__%s_sum" % field_id
                }
            ],
        },
        'key_entity_expression': field['key_entity_expression'],
        'format': field['format'],
    }

    # Save to overall quantity fields, 
    # and sasi_quantity fields.
    quantity_fields[qfield_id] = qfield
    sasi_quantity_fields[qfield_id] = qfield

# 
# Category Fields.
# Category fields represent x-values in a chart, or categories in a facet.
# They describe key/label entities, and query alterations.
#
category_fields = {}

# Define category fields for SASI categorical fields.
for field_id, field in sasi_categorical_fields.items():
    category_fields[field_id] = {
        'KEY': field.get('KEY'),
        'inner_query': field.get('inner_query'),
        'outer_query': field.get('outer_query'),
    }


# Define category fields for SASI numerical fields.
for field_id, field in sasi_quantity_fields.items():
    key_entity_id = 'facet%s_key_' % field_id
    key_entity = {
        'ID': key_entity_id,
        'EXPRESSION': field['key_entity_expression'],
        'AS_HISTOGRAM': True,
        'ALL_VALUES': True,
    }
    category_fields[field_id] = {
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
            'KEY_ENTITY': {'ID': 't', 'EXPRESSION': '__result__t'}
        },
        'value_type': 'numeric',
        'choices': [],
        'primary_filter_groups': ['scenario'],
        'filter_entity': {'TYPE': 'ENTITY', 'ID': 't',
                          'EXPRESSION': '__result__t'},
        'noClose': True
    },
}

# Facets for categorical category fields.
for field_id, field in sasi_categorical_fields.items():
    facet_def = {
        'label': field.get('label'),
        'info': field.get('info'),
        'info_link': field.get('info_link'),
        'type': 'list',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': field.get('filter_entity')
    }
    facet_def.update(category_fields[field_id])
    facets['definitions'][field_id] = {
        'id': field_id,
        'facetDef': facet_def,
    }

# Facets for SASI quantity fields
for qfield_id, qfield in sasi_quantity_fields.items():
    facet_def = {
        'label': qfield['label'],
        'info': qfield.get('info'),
        'info_link': qfield.get('info_link'),
        'type': 'numeric',
        'primary_filter_groups': ['data'],
        'base_filter_groups': ['scenario'],
        'filter_entity': {
            'TYPE': 'ENTITY', 
            'EXPRESSION': qfield['key_entity_expression'],
        },
        # TODO: set this for ranges.
        'range_auto': True
    }
    facet_def.update(category_fields[qfield_id])
    facets['definitions'][qfield_id] = {
        'id': qfield_id,
        'facetDef': facet_def,
    }

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

# SASI categorical fields category fields.
for field_id, field in sasi_categorical_fields.items():
    chart_category_field =  {
        'id': field_id,
        'label': field['label'],
        'value_type': 'categorical',
    }
    chart_category_field.update(category_fields[field_id])
    charts['category_fields'].append(chart_category_field)


# SASI quantity field category fields.
for field_id, field in sasi_quantity_fields.items():
    chart_category_field =  {
        'id': field_id,
        'label': field['label'],
        'value_type': 'numeric',
    }
    chart_category_field.update(category_fields[field_id])
    charts['category_fields'].append(chart_category_field)

app_config['charts'] = charts


#
# Maps.
#

data_layers = []
for field_id, field in sasi_numeric_fields.items():
    data_layer = {
        "id": field_id,
        "label": "%s (density)" % field['label'],
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
                    'ID': "%s_data" % field_id, 
                    'EXPRESSION': "func.sum(__result__%s)" % field_id,
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
                    'ID': "%s_geom_id" % field_id, 
                    'EXPRESSION': "__cell__id",
                },
                {
                    'ID': "%s_geom" % field_id, 
                    'EXPRESSION': "__cell__geom",
                },
                {
                    'ID': "%s_data" % field_id, 
                    'EXPRESSION': "__inner__%s_data / __cell__area" % field_id
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
        "geom_id_entity": {'ID': "%s_geom_id" % field_id},
        "geom_entity": {'ID': "%s_geom" % field_id},
        "data_entity": {
            'ID': "%s_data" % field_id,
            'min': 0,
            'max': 1,
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
                    "id":"result_znet_sum"
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
                            "defId":"substrate",
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
                                        "id":"substrate"
                                    },
                                    "quantityField":{
                                        "id":"result_znet_sum"
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
