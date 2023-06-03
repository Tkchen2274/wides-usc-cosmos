import os
dirname = os.path.dirname(os.path.abspath(__file__))

class Tx(object):

    __instance = None
    bias_ctrl_default = 0x1FFFF
    trx_sw_ctrl = None
    eder_version = '2'

    def __new__(cls, eder_version='2'):
        if cls.__instance is None:
            cls.__instance = super(Tx, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance


    def __init__(self, eder_version='2'):
        if self.__initialized:
            return
        self.__initialized = True
        import bf
        import register
        import memory
        import gpio
        import tx_dco
        import eder_logger
	import eder_status
        self.eder_version = eder_version
        self.regs = register.Register()
        self.mems = memory.Memory()
        self.gpio  = gpio.EderGpio(self.regs.board_type)
        self.bf   = bf.Bf(bf.Bf.TX)
        self.dco  = tx_dco.TxDco()
        self.logger = eder_logger.EderLogger()
        self.status = eder_status.EderStatus()

    def __default(self):
        self.regs.wr('bias_ctrl_tx',self.regs.value('bias_ctrl_tx'))
        self.regs.wr('bias_ctrl',self.regs.value('bias_ctrl'))
        self.regs.wr('bias_tx',self.regs.value('bias_tx'))
        self.regs.clr('bias_lo',0x08)
        self.regs.wr('tx_rf_mix_dc_lvl',self.regs.value('tx_rf_mix_dc_lvl'))
        self.regs.wr('tx_bb_ctrl',self.regs.value('tx_bb_ctrl'))
        self.regs.wr('tx_bb_gain',self.regs.value('tx_bb_gain'))
        self.regs.wr('tx_bb_phase',self.regs.value('tx_bb_phase'))
        self.regs.wr('tx_bb_iq_gain',self.regs.value('tx_bb_iq_gain'))
        self.regs.wr('tx_rf_gain',self.regs.value('tx_rf_gain'))
        self.regs.wr('tx_bf_gain',self.regs.value('tx_bf_gain'))


    def set_beam(self, beam):
        restore_tx_rx_sw_ctrl = self.regs.rd('tx_rx_sw_ctrl')
        self.regs.wr('tx_rx_sw_ctrl', 0b100)
        if beam != None:
            self.bf.awv.set(beam)
        else:
            self.bf.awv.set(self.bf.awv.get())
        self.regs.wr('tx_rx_sw_ctrl',restore_tx_rx_sw_ctrl)


    def reset(self):
        self.__default()
        self.status.clr_init_bit(self.status.TX_INIT)
        self.bias_ctrl_default = 0x1FFFF
        self.trx_sw_ctrl = None
        self.logger.log_info('TX Reset',2)


    def init(self, bias_ctrl_tx=bias_ctrl_default):
        if self.status.init_bit_is_set(self.status.TX_INIT) == False:
            self.regs.wr('bias_ctrl_tx',bias_ctrl_tx)
            self.regs.wr('bias_ctrl',0x1F)
            self.regs.wr('tx_rf_mix_dc_lvl',0x4)
            self.regs.wr('tx_bb_gain',0x00)
            self.regs.wr('tx_bb_phase',0x00)
            self.regs.wr('tx_bb_iq_gain',0xFF)
            if self.eder_version == '1':
                self.regs.wr('bias_tx',0xA7A9)
                self.regs.set('bias_lo',0x08)
                self.regs.wr('tx_rf_gain',0x00)
                self.regs.wr('tx_bb_ctrl',0x23)
                self.regs.wr('tx_bf_gain',0x0F)
            elif self.eder_version == '2':
                self.regs.wr('bias_tx',0xA7AA)
                self.regs.set('bias_lo',0x0A)
                self.regs.wr('tx_rf_gain',0x08)
                self.regs.wr('tx_bb_ctrl',0x37)
                self.regs.wr('tx_bb_phase',0x1F)
                self.regs.wr('tx_bf_gain',0x09)
            self.set_beam(31)
            self.status.set_init_bit(self.status.TX_INIT)
            self.logger.log_info('TX Initialised',2)


    def setup(self, freq, beam=None, bias_ctrl_tx=bias_ctrl_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 resets bf_tx_awv
        self.freq = freq
        self.bf.awv.setup(os.path.join(dirname, 'lut/beambook/bf_tx_awv_' + self.eder_version), freq, 0.0)
        self.bf.idx.setup(os.path.join(dirname, 'lut/beambook/bf_tx_awv_idx_' + self.eder_version), freq)

        self.init(bias_ctrl_tx)
        self.set_beam(beam)
        self.logger.log_info('TX Setup completed',2)


    def enable(self, beam=None):
        if self.trx_sw_ctrl == None:
            if (self.regs.rd('tx_rx_sw_ctrl') & 1):
                self.trx_sw_ctrl = 'HW'
            else:
                self.trx_sw_ctrl = 'SW'

        if self.trx_sw_ctrl == 'HW':
            self.gpio.set_tx_mode();
        else:
            self.regs.set('tx_rx_sw_ctrl', 0b100)

        self.set_beam(beam)
        self.logger.log_info('TX enabled',2)
        
            
    def disable(self):
        if self.trx_sw_ctrl == None:
            if (self.regs.rd('tx_rx_sw_ctrl') & 1):
                self.trx_sw_ctrl = 'HW'
            else:
                self.trx_sw_ctrl = 'SW'

        self.regs.clr('tx_rx_sw_ctrl', 0b100)
        self.logger.log_info('TX disabled',2)


    def hw_sw_enable(self):
        self.regs.set('tx_rx_sw_ctrl',0b001)
        self.trx_sw_ctrl = 'HW'

    def hw_sw_disable(self):
        self.regs.clr('tx_rx_sw_ctrl',0b001)
        self.trx_sw_ctrl = 'SW'
