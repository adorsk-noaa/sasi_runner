class ModelParameters(object):
    def __init__(self, time_start=None, time_end=None, time_step=None,
                 t_0=None, t_1=None, t_2=None, t_3=None, 
                 w_0=None, w_1=None, w_2=None, w_3=None,
                 projection=None):
        self.time_start = time_start
        self.time_end = time_end
        self.time_step = time_step
        self.t_0 = t_0
        self.t_1 = t_1
        self.t_2 = t_2
        self.t_3 = t_3
        self.w_0 = w_0
        self.w_1 = w_1
        self.w_2 = w_2
        self.w_3 = w_3
        self.projection = projection
