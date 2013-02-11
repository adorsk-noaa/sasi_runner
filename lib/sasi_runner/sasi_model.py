import logging


class SASI_Model(object):

    def __init__(self, t0=0, tf=10, dt=1, taus=None, omegas=None, dao=None, 
                 logger=logging.getLogger(), effort_model='nominal', 
                 result_fields=None, **kwargs):

        self.logger = logger

        self.t0 = t0 # Start time
        self.tf = tf # End time
        self.dt = dt # Time step
        # tau (recovery modifier)
        if not taus:
            taus = {
                    '0' : 1,
                    '1' : 2,
                    '2' : 5,
                    '3' : 10
                    }
        self.taus = taus

        # omega (damage modifier)
        if not omegas:
            omegas = {
                    '0' : .10,
                    '1' : .25,
                    '2' : .50,
                    '3' : 1
                    }
        self.omegas = omegas

        # Keys to use for identifying the results.
        # More fields improve the resolution of SASI results,
        # e.g. you can filter by both gear and substrate
        # but can greatly increase the number of results.
        if not result_fields:
            result_fields = ['gear_id', 'substrate_id', 'energy_id',
                             'feature_id', 'feature_category_id']
        self.result_fields = result_fields

        self.dao = dao

        self.effort_model = effort_model

        self.table_counters = {
            'SasiResult': 0,
            'FishingResult': 0,
        }

        self.setup()

    def setup(self):
        """
        Create in-memory look-ups to speed things up.
        """

        # Create va lookup.
        self.vas = {}
        for va in self.dao.query('__VA').all():
            key = (va.gear_id, va.substrate_id, va.energy_id, va.feature_id)
            self.vas[key] = va

        # Group habitat types by gears to which they can be applied.
        self.logger.info("Grouping habitats by gears...")
        self.ht_by_g = {} 
        for va in self.vas.values():
            ht = (va.substrate_id, va.energy_id,)
            gear_hts = self.ht_by_g.setdefault(va.gear_id, set())
            gear_hts.add(ht)

        # Group features by gears to which they can be applied.
        self.logger.info("Grouping features by gears...")
        self.f_by_g = {}
        for va in self.vas.values():
            gear_fs = self.f_by_g.setdefault(va.gear_id, set())
            gear_fs.add(va.feature_id)

        # Create feature lookup.
        self.logger.info("Creating features lookup...")
        self.features = {}
        for f in self.dao.query('__Feature').all():
            self.features[f.id] = f

        # Create gears lookups.
        self.logger.info("Creating gears lookup...")
        self.gears = {}
        self.generic_gears = {}
        for g in self.dao.query('__Gear').all():
            self.gears[g.id] = g
            if g.is_generic:
                self.generic_gears[g.id] = g

        # Group features by category and habitat types.
        self.logger.info("Grouping features by categories and habitats...")
        self.f_by_ht_fc = {}
        for va in self.vas.values():
            ht = (va.substrate_id, va.energy_id,)
            ht_fcs = self.f_by_ht_fc.setdefault(ht, {})
            f = self.features[va.feature_id]
            fc = f.category
            fc_fs = ht_fcs.setdefault(fc, set())
            fc_fs.add(va.feature_id)


        # Create cells-habitat_type-feature_category-feature lookup.
        self.c_ht_fc_f = self.get_c_ht_fc_f_lookup()

    def get_c_ht_fc_f_lookup(self):
        """ Create cells-habitat_type-feature_category-feature lookup. """

        self.logger.info(("Creating cells-habitat_type-feature_category-"
                          "feature lookup..."))
        c_ht_fc_f = {}
        for c in self.dao.query('__Cell').all():
            c_ht_fc_f[c.id] = { 'ht': {} }
            for ht, pct_area in c.habitat_composition.items():
                c_ht_fc_f[c.id]['ht'][ht] = {
                    'area': pct_area * c.area,
                    'fc': {}
                }
                for fc, fs in self.f_by_ht_fc[ht].items():
                    c_ht_fc_f[c.id]['ht'][ht]['fc'][fc] = fs
        return c_ht_fc_f

    def run(self, log_interval=1, commit=True, batch_size=20, **kwargs):
        self.run_counter = 0

        self.logger.info("Iterating through cells...")
        self.logger.info("Saving results every %s cells" % batch_size)
        Cell = self.dao.schema['sources']['Cell']
        cell_q = self.dao.session.query(Cell).order_by(Cell.id)
        batched_cell_q = self.dao.get_batched_results(cell_q, 1e2)

        # We partition into batches cells to avoid overloading memory.
        # 'Cuz there can be a lotta data.
        batch_counter = 0
        cell_batch = []
        self.num_cells = cell_q.count()
        for c in batched_cell_q:
            batch_counter += 1
            cell_batch.append(c)

            # Fill up a batch before procesing.
            if (batch_counter % batch_size) == 0:
                self.run_batch(cell_batch, log_interval=log_interval)
                batch_counter = 0
                cell_batch = []

        # Process remaining cells.
        self.run_batch(cell_batch, log_interval=log_interval)

        self.logger.info('Run completed.')

    def run_batch(self, cell_batch, commit=True, log_interval=1):
        # Set of current fields for result keys.
        result_fields = {}

        # Get a local cache of results and efforts for the current batch.
        sasi_result_cache = self.get_result_cache(cell_batch)
        fishing_result_cache = self.get_result_cache(cell_batch)
        effort_cache = self.get_effort_cache(cell_batch)

        for cell in cell_batch:
            self.run_counter += 1
            # Shortcut.
            c = cell.id

            if (self.run_counter % log_interval) == 0: 
                self.logger.info("cell #%d of %d (%.1f%%)" % (
                   self.run_counter, self.num_cells, 
                   1.0 * self.run_counter/self.num_cells * 100))

            for t in range(self.t0, self.tf + 1, self.dt):
                for effort in effort_cache.get(c, {}).get(t, []):

                    gear = self.gears.get(effort.gear_id)
                    generic_gear = self.generic_gears.get(gear.generic_id)

                    # Add raw effort fields to fishing results, by generic gear
                    # and specific gear (if not generic).
                    gear_ids = [gear.id]
                    if generic_gear is not gear:
                        gear_ids.append(generic_gear.id)
                    for gear_id in gear_ids:
                        fishing_result = self.get_or_create_fishing_result(
                            fishing_result_cache, t, c, gear_id, generic_gear.id)
                        for field in ['value', 'hours_fished', 'a']:
                            old_val = getattr(fishing_result, field, None)
                            if old_val is None:
                                old_val = 0.0
                            effort_val = getattr(effort, field, None) 
                            if effort_val is None:
                                effort_val = 0.0
                            setattr(fishing_result, field, old_val + effort_val)

                    # If effort gear has depth limits, skip if cell depth is not
                    # w/in the limits.
                    if not generic_gear:
                        continue
                    if generic_gear.min_depth is not None \
                       and cell.depth < generic_gear.min_depth:
                        continue
                    if gear.max_depth is not None \
                       and cell.depth > generic_gear.max_depth:
                        continue
                    result_fields['gear_id'] = generic_gear.id

                    # Get relevant habitat types for the effort.
                    relevant_habitat_types = []
                    for ht in self.c_ht_fc_f[c]['ht'].keys():
                        if ht in self.ht_by_g.get(generic_gear.id, {}): 
                            relevant_habitat_types.append(ht)

                    # Skip if no relevant habitat types.
                    if not relevant_habitat_types:
                        continue

                    # Get combined area of relevant habitats.
                    relevant_habitats_area = sum(
                        [self.c_ht_fc_f[c]['ht'][ht]['area'] 
                         for ht in relevant_habitat_types])

                    # For each relevant habitat...
                    for ht in relevant_habitat_types:
                        result_fields.update({
                            'substrate_id': ht[0],
                            'energy_id': ht[1],
                        })

                        # Calculate percentage of habitat 
                        # type's area as a fraction of the total relevant
                        # area.
                        ht_area = self.c_ht_fc_f[c]['ht'][ht]['area']
                        ht_pct = ht_area/relevant_habitats_area

                        # Get feature categories for habitat type.
                        fcs = self.c_ht_fc_f[c]['ht'][ht]['fc'].keys()

                        # Skip if no feature categories.
                        if not fcs:
                            continue

                        # Calculate percentage of values that should be
                        # distribute to each feature category.
                        fc_pct = ht_pct/len(fcs)

                        for fc in fcs:
                            result_fields['feature_category_id'] = fc
                            relevant_features = []
                            for f in self.c_ht_fc_f[c]['ht'][ht]['fc'][fc]:
                                if f in self.f_by_g[generic_gear.id]: 
                                    relevant_features.append(f)

                            # Skip if no relevant features.
                            if not relevant_features:
                                continue

                            # Calculate percentage of values that should be
                            # distributed to each feature.
                            pct_f = fc_pct/len(relevant_features)

                            for f in relevant_features:
                                result_fields['feature_id'] = f

                                # Get vulnerability assessment for the effort.
                                va = self.vas[(generic_gear.id, ht[0], ht[1], f)]

                                omega = self.omegas[va.s]
                                tau = self.taus[va.r]

                                result = self.get_or_create_result(
                                    sasi_result_cache, t, c, result_fields)

                                # Calculate swept area for the feature.
                                f_swept_area = pct_f * getattr(effort, 'a', 0.0)

                                # Add the resulting contact-adjusted
                                # swept area to the a field.
                                result.a += f_swept_area

                                # Calculate adverse effect swept area and add to y field.
                                adverse_effect_swept_area = f_swept_area * omega
                                result.y += adverse_effect_swept_area

                                # Calculate recovery per timestep.
                                if tau == 0:
                                    recovery_per_dt = 0
                                else:
                                    recovery_per_dt = adverse_effect_swept_area/tau

                                # Add recovery to x field for future entries.
                                for future_t in range(t + 1, t + tau + 1, self.dt):
                                    if future_t <= self.tf:
                                        future_result = self.get_or_create_result(
                                            sasi_result_cache, future_t, c,
                                            result_fields)
                                        future_result.x += recovery_per_dt

                                # Calculate Z.
                                result.z = result.x - result.y

                            # End of feature block
                    # End of habitats block
                    # End of efforts block

                # Update znet for timestep.
                for rkey, cur_r in sasi_result_cache[c][t].items():
                    if t == self.t0:
                        cur_r.znet = cur_r.z
                    else:
                        prev_r = self.get_or_create_result(
                            sasi_result_cache, t - self.dt, c, result_fields)
                        cur_r.znet = prev_r.znet + cur_r.z


                # Update fishing net fields.
                for rkey, cur_r in fishing_result_cache[c][t].items():
                    for field in ['value', 'hours_fished']:
                        net_field = field + '_net'
                        if t == self.t0:
                            setattr(cur_r, net_field, getattr(cur_r, field, 0))
                        else:
                            prev_r = self.get_or_create_fishing_result(
                                fishing_result_cache, t - self.dt, c, 
                                cur_r.gear_id, cur_r.generic_gear_id)
                            setattr(cur_r, net_field, 
                                    getattr(prev_r, net_field, 0))


                # End of timestep block
            # End of cell block

        # Save results.
        self.save_result_cache('SasiResult', sasi_result_cache, commit=commit)
        self.save_result_cache('FishingResult', fishing_result_cache, commit=commit)

    def save_result_cache(self, table, result_cache, commit=True):
        prev_num_saved = self.table_counters[table]

        def results_iter():
            for cell_results in result_cache.values():
                for time_results in cell_results.values():
                    for result in time_results.values():
                        self.table_counters[table] += 1
                        yield result

        self.logger.info("Saving partial results for '%s' table..." % table)
        self.dao.bulk_insert_objects(table, results_iter(), commit=commit)
        self.logger.info("%.3e results saved. (%.3e overall)" % (
            self.table_counters[table] - prev_num_saved, 
            self.table_counters[table]))

    def get_effort_cache(self, cells):
        """ Get efforts cache, grouped by cell and time. """
        effort_cache = {}
        efforts = []
        if self.effort_model == 'nominal':
            efforts = self.get_nominal_efforts(cells)
        else:
            cell_ids = [c.id for c in cells]
            Effort = self.dao.schema['sources']['Effort']
            effort_q = self.dao.session.query(Effort)
            efforts = effort_q.filter(Effort.cell_id.in_(cell_ids)).all()

        for effort in efforts:
            cell_efforts = effort_cache.setdefault(effort.cell_id, {})
            time_efforts = cell_efforts.setdefault(effort.time, [])
            time_efforts.append(effort)
        return effort_cache

    def get_nominal_efforts(self, cells):
        efforts = []
        Effort = self.dao.schema['sources']['Effort']
        num_gears = len(self.generic_gears)
        for t in range(self.t0, self.tf + 1, self.dt):
            for cell in cells:
                for gear in self.generic_gears.values():
                    efforts.append(
                        Effort(
                            cell_id=cell.id,
                            time=t,
                            a=cell.area/num_gears,
                            gear_id=gear.id
                        )
                    )
        return efforts

    def get_result_cache(self, cells):
        """ Get results cache, grouped by cell, time, and result key. """
        result_cache = {}
        for cell_id in [c.id for c in cells]:
            cell_results = result_cache.setdefault(cell_id, {})
            for t in range(self.t0, self.tf + 1, self.dt):
                time_results = cell_results.setdefault(t, {})
        return result_cache

    def get_or_create_result(self, result_cache, t, cell_id, fields):
        result_key = tuple(
            [t, cell_id] + [fields[f] for f in self.result_fields])
        relevant_fields = dict([(k,v) for k,v in fields.items() if k in
                                self.result_fields])
        if not result_cache[cell_id][t].has_key(result_key):
            new_result = self.dao.schema['sources']['SasiResult'](
                t=t,
                cell_id=cell_id,
                a=0.0,
                x=0.0,
                y=0.0,
                z=0.0,
                znet=0.0,
                **relevant_fields
            )
            result_cache[cell_id][t][result_key] = new_result
        return result_cache[cell_id][t][result_key]

    def get_or_create_fishing_result(self, result_cache, t, cell_id, gear_id,
                                     generic_gear_id):
        result_key = tuple([t, cell_id, gear_id])
        if not result_cache[cell_id][t].has_key(result_key):
            new_result = self.dao.schema['sources']['FishingResult'](
                t=t,
                cell_id=cell_id,
                gear_id=gear_id,
                generic_gear_id=generic_gear_id,
                value=0.0,
                value_net=0.0,
                hours_fished=0.0,
                hours_fished_net=0.0,
            )
            result_cache[cell_id][t][result_key] = new_result
        return result_cache[cell_id][t][result_key]
