import sasi_runner.util.shapefile as shapefile_util


class Shapefile_Ingestor(object):

    def __init__(self, shp_file=None, dao=None, clazz=None, mappings={},
                 geom_attr='geom', force_multipolygon=True):
        self.dao = dao
        self.clazz = clazz
        self.mappings = mappings
        self.reader = shapefile_util.get_shapefile_reader(shp_file)
        self.geom_attr = geom_attr
        self.force_multipolygon = force_multipolygon

    def ingest(self):
        fields = self.reader.fields
        shapetype = self.reader.shapetype
        if shapetype == 'POLYGON' and self.force_multipolygon:
            shapetype='MULTIPOLYGON'
        for record in self.reader.records():
            obj = self.clazz()

            for mapping in self.mappings:
                raw_value = record['properties'].get(mapping.get('source'))
                processor = mapping.get('processor')
                if not processor:
                    processor = lambda value: value
                value = processor(raw_value)
                setattr(obj, mapping['target'], value)

            wkt_parts = []
            for part in record['geometry']['coordinates']:
                wkt_points = ', '.join(["%s %s" % (point[0], point[1]) 
                              for point in part])
                wkt_part = "(%s)" % (wkt_points)
                wkt_parts.append(wkt_part)
            wkt_parts = ','.join(wkt_parts)
            wkt_geom = "%s((%s))" % (shapetype, wkt_parts)
            if self.geom_attr and hasattr(obj, self.geom_attr):
                setattr(obj, self.geom_attr, wkt_geom)

            self.dao.save(obj)
