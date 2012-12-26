import logging


class SASI_Model(object):

    def __init__(self, t0=0, tf=10, dt=1, taus=None, omegas=None, dao=None, 
                 logger=logging.getLogger(), batch_size=100, **kwargs):

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

        self.dao = dao

        self.batch_size = batch_size

        self.setup()

    def setup(self):
        """
        Create in-memory look-ups to speed things up.
        """

        vas = self.dao.query('__VA')

        # Create va lookup.
        self.va_lu = {}
        for va in vas:
            key = (va.gear_id, va.substrate_id, va.energy_id, va.feature_id)
            self.va_lu[key] = va

        # Group habitat types by gears to which they can be applied.
        self.logger.info("Grouping habitats by gears...")
        self.ht_by_g = {} 
        for va in vas:
            ht = (va.substrate_id, va.energy_id,)
            gear_hts = self.ht_by_g.setdefault(va.gear_id, set())
            gear_hts.add(ht)

        # Group features by gears to which they can be applied.
        self.logger.info("Grouping features by gears...")
        self.f_by_g = {}
        for va in vas:
            gear_fs = self.f_by_g.setdefault(va.gear_id, set())
            gear_fs.add(va.feature_id)

        # Create feature lookup.
        self.logger.info("Creating features lookup...")
        self.features_lu = {}
        for f in self.dao.query('__Feature'):
            self.features_lu[f.id] = f

        # Group features by category and habitat types.
        self.logger.info("Grouping features by categories and habitats...")
        self.f_by_ht_fc = {}
        for va in vas:
            ht = (va.substrate_id, va.energy_id,)
            ht_fcs = self.f_by_ht_fc.setdefault(ht, {})
            f = self.features_lu[va.feature_id]
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
        for c in self.dao.query('__Cell'):
            c_ht_fc_f[c.id] = { 'ht': {} }
            for ht, pct_area in c.habitat_composition.items():
                c_ht_fc_f[c.id]['ht'][ht] = {
                    'area': pct_area * c.area,
                    'fc': {}
                }
                for fc, fs in self.f_by_ht_fc[ht].items():
                    c_ht_fc_f[c.id]['ht'][ht]['fc'][fc] = fs
        return c_ht_fc_f

    def run(self, log_interval=1, commit=True, **kwargs):

        batch_size = kwargs.get('batch_size', getattr(self, 'batch_size', 100))

        self.logger.info("Iterating through cells...")
        # We partition by cells to avoid overloading memory.
        # 'Cuz there can be a lotta data...
        Cell = self.dao.schema['sources']['Cell']
        cell_q = self.dao.session.query(Cell).order_by(Cell.id)
        cell_counter = 0
        num_cells = cell_q.count()

        # Caches for cells, to speed up lookups.
        while cell_counter < num_cells:
            cell_batch = cell_q.offset(cell_counter).limit(batch_size).all()
            cell_ids = [cell.id for cell in cell_batch]

            # Get a local cache of results and efforts for the current batch.
            effort_cache = self.get_effort_cache(cell_ids)
            result_cache = self.get_result_cache(cell_ids)

            for c in cell_ids:

                cell_counter += 1
                if (cell_counter % log_interval) == 0: 
                   self.logger.info("cell #%d of %d (%.1f%%)" % (
                       cell_counter, num_cells, 1.0 * cell_counter/num_cells * 100))

                for t in range(self.t0, self.tf + 1, self.dt):
                    for effort in effort_cache.get(c, {}).get(t, []):

                        # Get relevant habitat types for the effort.
                        relevant_habitat_types = []
                        for ht in self.c_ht_fc_f[c]['ht'].keys():
                            if ht in self.ht_by_g.get(effort.gear_id, {}): 
                                relevant_habitat_types.append(ht)

                        if relevant_habitat_types:
                            # Get combined area of relevant habitats.
                            relevant_habitats_area = sum(
                                [self.c_ht_fc_f[c]['ht'][ht]['area'] 
                                 for ht in relevant_habitat_types])

                            # For each relevant habitat...
                            for ht in relevant_habitat_types:

                                # Distribute the effort's raw swept area 
                                # proportionally to the habitat type's area 
                                # as a fraction of the total relevant area.
                                ht_area = self.c_ht_fc_f[c]['ht'][ht]['area']
                                ht_swept_area = effort.a * (
                                    ht_area/relevant_habitats_area)

                                # Distribute swept area equally across feature categories.
                                fcs = self.c_ht_fc_f[c]['ht'][ht]['fc'].keys()
                                fc_swept_area = ht_swept_area/len(fcs)

                                for fc in fcs:

                                    relevant_features = []
                                    for f in self.c_ht_fc_f[c]['ht'][ht]['fc'][fc]:
                                        if f in self.f_by_g[effort.gear_id]: 
                                            relevant_features.append(f)

                                    if relevant_features:

                                        # Distribute the category's effort equally over the features.
                                        f_swept_area = fc_swept_area/len(relevant_features)

                                        for f in relevant_features:

                                            # Get vulnerability assessment for the effort.
                                            va = self.va_lu[(effort.gear_id, ht[0], ht[1], f)]

                                            omega = self.omegas[va.s]
                                            tau = self.taus[va.r]

                                            result_key = (
                                                ht[0], ht[1], effort.gear_id, f, fc
                                            )
                                            result = self.get_or_create_result(
                                                result_cache, t, c, result_key)

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
                                                        result_cache, future_t, c, result_key)
                                                    future_result.x += recovery_per_dt

                                            # Calculate Z.
                                            result.z = result.x - result.y

                                        # End of feature block
                            # End of habitats block
                        # End of efforts block

                    # Update znet for all results for timestep if not the
                    # first timestep.
                    for rkey, cur_r in result_cache[c][t].items():
                        if t == self.t0:
                            cur_r.znet = cur_r.z
                        else:
                            prev_r = self.get_or_create_result(
                                result_cache, t - self.dt, c, rkey)
                            cur_r.znet = prev_r.znet + cur_r.z
                    # End of timestep block
                # End of cell block

            # Save results.
            for cell_results in result_cache.values():
                for time_results in cell_results.values():
                    for result in time_results.values():
                        self.dao.save(result, commit=False)
            if commit:
                self.logger.info('saving partial results...')
                self.dao.commit()
            # End of batch block.
        self.logger.info('Run completed.')

    def get_effort_cache(self, cell_ids):
        """ Get efforts cache, grouped by cell and time. """
        effort_cache = {}
        Effort = self.dao.schema['sources']['Effort']
        effort_q = self.dao.session.query(Effort)
        efforts = effort_q.filter(Effort.cell_id.in_(cell_ids)).all()
        for effort in efforts:
            cell_efforts = effort_cache.setdefault(effort.cell_id, {})
            time_efforts = cell_efforts.setdefault(effort.time, [])
            time_efforts.append(effort)
        return effort_cache

    def get_result_cache(self, cell_ids):
        """ Get results cache, grouped by cell, time, and result key. """
        result_cache = {}
        for cell_id in cell_ids:
            cell_results = result_cache.setdefault(cell_id, {})
            for t in range(self.t0, self.tf + 1, self.dt):
                time_results = cell_results.setdefault(t, {})
        return result_cache

    def get_or_create_result(self, result_cache, t, cell_id, result_key):
        substrate_id = result_key[0]
        energy_id = result_key[1]
        gear_id = result_key[2]
        feature_id = result_key[3]
        feature_category_id = result_key[4]

        if not result_cache[cell_id][t].has_key(result_key):
            new_result = self.dao.schema['sources']['Result'](
                t=t,
                cell_id=cell_id,
                gear_id=gear_id,
                substrate_id=substrate_id,
                energy_id=energy_id,
                feature_id=feature_id,
                feature_category_id=feature_category_id,
                a=0.0,
                x=0.0,
                y=0.0,
                z=0.0,
                znet=0.0,
            )
            result_cache[cell_id][t][result_key] = new_result

        return result_cache[cell_id][t][result_key]
