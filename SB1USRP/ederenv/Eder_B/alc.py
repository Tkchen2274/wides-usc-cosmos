class ALC(object):


    def __init__(self):
        import register
        
        self.regs = register.Register()
        
    def init(self, tx_alc_pdet_lo_th=0, tx_alc_pdet_hi_offs_th=0):
        self.regs.write('tx_alc_loop_cnt', 0)
        self.regs.write('tx_alc_start_delay', 224) # 1 microsecond at 225MHz
        self.regs.write('tx_alc_meas_delay', 24)   # 100 nanoseconds at 225MHz
        self.regs.write('tx_alc_bfrf_gain_max', 0xff)
        self.regs.write('tx_alc_bfrf_gain_min' 0x00)
        self.regs.write('tx_alc_step_max', 0x01)
        self.regs.write('tx_alc_pdet_lo_th', tx_alc_pdet_lo_th)
        self.regs.write('tx_alc_pdet_hi_offs_th', tx_alc_pdet_hi_offs_th)
        self.regs.write('tx_alc_ctrl', 0xd0)
    
    def enable(self):
        self.regs.set('tx_alc_ctrl', 0x01)
        
    def disable(self):
        self.regs.clear('tx_alc_ctrl', 0x01)
    
    def start(self, pdet_mux, alc_mux):
        self.regs.write('tx_bf_pdet_mux', 0x80 + (pdet_mux & 0x0f) + ((alc_mux & 0x30) << 4)
        self.regs.toggle('tx_alc_ctrl', 0x02)
    
