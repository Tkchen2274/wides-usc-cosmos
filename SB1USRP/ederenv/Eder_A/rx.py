class Rx(object):

    __instance = None
    bias_ctrl_default = 0x1FFFF
    trx_sw_ctrl = None
    eder_version = '2'

    def __new__(cls, eder_version='2'):
        if cls.__instance is None:
            cls.__instance = super(Rx, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, eder_version='2'):
        if self.__initialized:
            return
        self.__initialized = True
        import bf
        import agc
        import adc
        import pll
        import rx_dco
        import temp
        import register
        import memory
        import gpio
        import eder_logger
        import eder_status
        self.regs = register.Register()
        self.mems = memory.Memory()
        self.gpio  = gpio.EderGpio(self.regs.board_type)
        self.bf   = bf.Bf(bf.Bf.RX)
        self.agc  = agc.Agc()
        self.adc  = adc.Adc()
        self.pll  = pll.Pll()
        self.dco = rx_dco.RxDco()
        self.temp = temp.Temp()
        self.logger = eder_logger.EderLogger()
        self.status = eder_status.EderStatus()
        #

    def __default(self):
        self.regs.wr('bias_ctrl_rx',self.regs.value('bias_ctrl_rx'))
        self.regs.wr('bias_rx',self.regs.value('bias_rx'))
        self.regs.clr('bias_lo',0x20)
        self.regs.wr('rx_bb_biastrim',self.regs.value('rx_bb_biastrim'))
        self.regs.wr('rx_bb_en',self.regs.value('rx_bb_en'))
        self.regs.wr('rx_bb_i_vga_1_2',self.regs.value('rx_bb_i_vga_1_2'))
        self.regs.wr('rx_bb_q_vga_1_2',self.regs.value('rx_bb_q_vga_1_2'))
        self.regs.wr('rx_bb_i_vga_1db',self.regs.value('rx_bb_i_vga_1db'))
        self.regs.wr('rx_bb_q_vga_1db',self.regs.value('rx_bb_q_vga_1db'))
        self.regs.wr('rx_bf_rf_gain',self.regs.value('rx_bf_rf_gain'))
        self.dco.default()

    def set_beam(self, beam):
        restore_tx_rx_sw_ctrl = self.regs.rd('tx_rx_sw_ctrl')
        self.regs.wr('tx_rx_sw_ctrl', 0b010)
        if beam != None:
            self.bf.awv.set(beam)
        else:
            self.bf.awv.set(self.bf.awv.get())
        self.regs.wr('tx_rx_sw_ctrl',restore_tx_rx_sw_ctrl)


    def reset(self):
        self.__default()
        self.status.clr_init_bit(self.status.RX_INIT)
        self.bias_ctrl_default = 0x1FFFF
        self.trx_sw_ctrl = None
        self.logger.log_info('RX Reset',2)
    

    def init(self, bias_ctrl_rx=bias_ctrl_default):
        if self.status.init_bit_is_set(self.status.RX_INIT) == False:
            self.regs.wr('bias_ctrl_rx',bias_ctrl_rx)
            self.regs.wr('bias_rx',0x0AAB)
            self.regs.set('bias_lo',0x20)
            self.regs.wr('rx_bb_biastrim',0x00)
            self.regs.wr('rx_bb_en',0xBF)
            if self.eder_version == '1':
                self.regs.wr('rx_bb_i_vga_1_2',0x7F)
                self.regs.wr('rx_bb_q_vga_1_2',0x7F)
                self.regs.wr('rx_bb_i_vga_1db',0x0F)
                self.regs.wr('rx_bb_q_vga_1db',0x0F)
                self.regs.wr('rx_bf_rf_gain',0xFF)
            elif self.eder_version == '2':
                self.regs.wr('rx_bb_i_vga_1_2',0x73)
                self.regs.wr('rx_bb_q_vga_1_2',0x73)
                self.regs.wr('rx_bb_i_vga_1db',0x0E)
                self.regs.wr('rx_bb_q_vga_1db',0x0E)
                self.regs.wr('rx_bf_rf_gain',0xEE)
            self.set_beam(31)
            self.status.set_init_bit(self.status.RX_INIT)
            self.logger.log_info('RX Initialised',2)

    def setup(self, freq, beam=None, bias_ctrl_rx=bias_ctrl_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 fills bf_rx_awv with zeros
        self.bf.awv.setup('lut/beambook/bf_rx_awv_' + self.eder_version, freq, 0.0)
        self.bf.idx.setup('lut/beambook/bf_rx_awv_idx_' + self.eder_version, freq)

        self.init(bias_ctrl_rx)
        self.set_beam(beam)

        import time
        print 'Wait for temperature stabilization'
        previous_temp = 0
        current_temp = self.temp.run()

        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(5)
                current_temp = self.temp.run()
                print 'temp: {0} C'.format(round(current_temp-273.15,2))

        print 'Temperature stabilized'

        self.dco.run()
        self.logger.log_info('RX Setup completed',2)

    def setup_no_dco_cal(self, freq, beam=None, bias_ctrl_rx=bias_ctrl_default):
        self.freq = freq
        # Import beamforming table and write to memory
        # TODO: Here we should prepare for writing the beambook
        # freq 0.0 and temp 0.0 fills bf_rx_awv with zeros
        self.bf.awv.setup('lut/beambook/bf_rx_awv_' + self.eder_version, freq, 0.0)
        self.bf.idx.setup('lut/beambook/bf_rx_awv_idx_' + self.eder_version, freq)
        self.init(bias_ctrl_rx)
        self.set_beam(beam)
        self.logger.log_info('RX Setup completed',2)



    def enable(self, beam=None):
        if self.trx_sw_ctrl == None:
            if (self.regs.rd('tx_rx_sw_ctrl') & 1):
                self.trx_sw_ctrl = 'HW'
            else:
                self.trx_sw_ctrl = 'SW'

        if self.trx_sw_ctrl == 'HW':
            self.gpio.set_rx_mode();
        else:
            self.regs.set('tx_rx_sw_ctrl', 0b010)

        self.set_beam(beam)
        self.logger.log_info('RX enabled',2)

            

    def disable(self):
        if self.trx_sw_ctrl == None:
            if (self.regs.rd('tx_rx_sw_ctrl') & 1):
                self.trx_sw_ctrl = 'HW'
            else:
                self.trx_sw_ctrl = 'SW'

        self.regs.clr('tx_rx_sw_ctrl', 0b010)


    def hw_sw_enable(self):
        self.regs.set('tx_rx_sw_ctrl',0b001)
        self.trx_sw_ctrl = 'HW'

    def hw_sw_disable(self):
        self.regs.clr('tx_rx_sw_ctrl',0b001)
        self.trx_sw_ctrl = 'SW'


    def gain_set(self, stage, gain):
        if isinstance(stage,list):
            gain  = stage
            if len(gain) == 3:
                stage = 'bfrf123'
            if len(gain) == 2:
                stage = '123'
            
        if stage == 'rf':
            gain_rd = self.regs.rd('rx_bf_rf_gain')
            self.regs.wr('rx_bf_rf_gain', (gain_rd & 0xF0) | (gain & 0x0F))
        if stage == 'bf':
            gain_rd = self.regs.rd('rx_bf_rf_gain')
            self.regs.wr('rx_bf_rf_gain', (gain_rd & 0x0F) | ((gain & 0x0F)<<4))
        if stage == 'bfrf':
            self.regs.wr('rx_bf_rf_gain', gain)
        if stage == '1':
            gain_rd_i = self.regs.rd('rx_bb_i_vga_1_2')
            gain_rd_q = self.regs.rd('rx_bb_q_vga_1_2')
            self.regs.wr('rx_bb_i_vga_1_2', (gain_rd_i & 0x0F) | ((gain & 0x0F)<<4))
            self.regs.wr('rx_bb_q_vga_1_2', (gain_rd_q & 0x0F) | ((gain & 0x0F)<<4))
        if stage == '2':
            gain_rd_i = self.regs.rd('rx_bb_i_vga_1_2')
            gain_rd_q = self.regs.rd('rx_bb_q_vga_1_2')
            self.regs.wr('rx_bb_i_vga_1_2', (gain_rd_i & 0xF0) | (gain & 0x0F))
            self.regs.wr('rx_bb_q_vga_1_2', (gain_rd_q & 0xF0) | (gain & 0x0F))
        if stage == '3':
            self.regs.wr('rx_bb_i_vga_1db', gain)
            self.regs.wr('rx_bb_q_vga_1db', gain)
        if stage == '12':
            self.regs.wr('rx_bb_i_vga_1_2', gain)
            self.regs.wr('rx_bb_q_vga_1_2', gain)
        if stage == '123':
            self.regs.wr('rx_bb_i_vga_1_2', gain[0])
            self.regs.wr('rx_bb_q_vga_1_2', gain[0])
            self.regs.wr('rx_bb_i_vga_1db', gain[1])
            self.regs.wr('rx_bb_q_vga_1db', gain[1])
        if stage == 'bfrf123':
            self.regs.wr('rx_bf_rf_gain',   gain[0])
            self.regs.wr('rx_bb_i_vga_1_2', gain[1])
            self.regs.wr('rx_bb_q_vga_1_2', gain[1])
            self.regs.wr('rx_bb_i_vga_1db', gain[2])
            self.regs.wr('rx_bb_q_vga_1db', gain[2])

    def gain_get(self, stage=None):
        if stage == None:
            stage = 'bfrf123'
        if stage == 'rf':
            return self.regs.rd('rx_bf_rf_gain') & 0x0F
        if stage == 'bf':
            return (self.regs.rd('rx_bf_rf_gain') & 0xF0)>>4
        if stage == 'bfrf':
            return self.regs.rd('rx_bf_rf_gain')
        if stage == '1':
            return (self.regs.rd('rx_bb_q_vga_1_2') & 0xF0) >> 4, (self.regs.rd('rx_bb_i_vga_1_2') & 0xF0) >> 4
        if stage == '2':
            return self.regs.rd('rx_bb_q_vga_1_2') & 0x0F, self.regs.rd('rx_bb_i_vga_1_2') & 0x0F
        if stage == '3':
            return self.regs.rd('rx_bb_q_vga_1db', gain), self.regs.rd('rx_bb_i_vga_1db', gain)
        if stage == '12':
            return self.regs.rd('rx_bb_q_vga_1_2'), self.regs.rd('rx_bb_i_vga_1_2')
        if stage == '123':
            return self.regs.rd('rx_bb_q_vga_1_2'), self.regs.rd('rx_bb_i_vga_1_2'), self.regs.rd('rx_bb_q_vga_1db', gain), self.regs.rd('rx_bb_i_vga_1db', gain)
        if stage == 'bfrf123':
            return self.regs.rd('rx_bf_rf_gain'), self.regs.rd('rx_bb_q_vga_1_2'), self.regs.rd('rx_bb_i_vga_1_2'), self.regs.rd('rx_bb_q_vga_1db'), self.regs.rd('rx_bb_i_vga_1db')

