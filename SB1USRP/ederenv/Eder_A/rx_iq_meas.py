class RxIQMeas(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(RxIQMeas, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import adc
        import amux
        self.__initialized = True
        self.regs = register.Register()
        self.amux  = amux.Amux(self.regs)
        self.adc  = adc.Adc()
        self.meas_amp_vcm = self._read_adc(self.amux.amux_dco_cm)

    def init(self):
        self.adc.init()
        self.meas_amp_vcm = self._read_adc(self.amux.amux_dco_cm)

    def reset(self):
        self.adc.reset()

    def _read_adc(self, src1, src2=None, num_samples=16):
        self.adc.start(src1, src2)
        adc_value = self.adc.mean(self.adc.dump(num_samples))
        self.adc.stop()
        return adc_value


    def meas(self, num_samples=16, meas_type='sys'):
        if meas_type == 'bb':
            vdiff = dict()
            vcm =  dict()
            vals = {}
            amux_set = {'i_p':self.amux.rx_bb_outb_dc_p_i,
                        'q_p':self.amux.rx_bb_outb_dc_p_q,
                        'i_n':self.amux.rx_bb_outb_dc_n_i,
                        'q_n':self.amux.rx_bb_outb_dc_n_q}
            for key, val in amux_set.iteritems():
                vals[key] = self._read_adc(self.amux.amux_rx_bb, val, num_samples)

            vdiff['idiff'] = vals['i_p']-vals['i_n']
            vdiff['qdiff'] = vals['q_p']-vals['q_n']
            vcm['icm']     = (vals['i_p']+vals['i_n'])/2
            vcm['qcm']     = (vals['q_p']+vals['q_n'])/2
        else:
            vcm   = self.meas_vcm(num_samples)
            vdiff = self.meas_vdiff(num_samples, meas_type)
            
        return {'idiff':vdiff['idiff'], 'qdiff':vdiff['qdiff'], 'icm':vcm['icm'], 'qcm':vcm['qcm']}


    def meas_vcm(self, num_samples=16):
        vals = {}
        amux_set = {'i_p':self.amux.rx_bb_outb_dc_p_i,
                    'q_p':self.amux.rx_bb_outb_dc_p_q,
                    'i_n':self.amux.rx_bb_outb_dc_n_i,
                    'q_n':self.amux.rx_bb_outb_dc_n_q}
        for key, val in amux_set.iteritems():
            vals[key] = self._read_adc(self.amux.amux_rx_bb, val, num_samples)
        vicm   = (vals['i_p']+vals['i_n'])/2
        vqcm   = (vals['q_p']+vals['q_n'])/2
            
        return {'icm':vicm, 'qcm':vqcm}


    def meas_vdiff(self, num_samples=16, meas_type='sys', meas_cm='Yes'):
        if meas_type == 'bb':
            vals = {}
            amux_set = {'i_p':self.amux.rx_bb_outb_dc_p_i,
                        'q_p':self.amux.rx_bb_outb_dc_p_q,
                        'i_n':self.amux.rx_bb_outb_dc_n_i,
                        'q_n':self.amux.rx_bb_outb_dc_n_q}
            for key, val in amux_set.iteritems():
                vals[key] = self._read_adc(self.amux.amux_rx_bb, val, num_samples)
            vidiff = vals['i_p']-vals['i_n']
            vqdiff = vals['q_p']-vals['q_n']
        else:
            if meas_cm == 'Yes':
                self.meas_amp_vcm = self._read_adc(self.amux.amux_dco_cm, None, num_samples)

            vidiff = self._read_adc(self.amux.amux_dco_i, None, num_samples) - self.meas_amp_vcm
            vqdiff = self._read_adc(self.amux.amux_dco_q, None, num_samples) - self.meas_amp_vcm
            
        return {'idiff':vidiff, 'qdiff':vqdiff}
