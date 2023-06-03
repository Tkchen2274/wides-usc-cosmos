import sys
import time
import math
from threading import Timer
class Eder:
    import csv
    import background
    import common

    def __init__(self, init=False, backgr=True, log_instance=None, unit_name='Motherboard 1', board_type='MB1', eder_version='2'):
        import gpio
        import register
        import memory
        import ref
        import vco
        import pll
        import adc
        import bf
        import temp
        import eeprom        
        import rx
        import tx
        import eder_status
        import eder_logger

        self.board_type = board_type
        self.pdet_bias = None

        if self.board_type == 'MB1':
            try:
                import ederftdi
                self.ederftdi = ederftdi
                if self.ederftdi.init(unit_name) != 0:
			print '  Device initialization failed!'
			return
		self.ederftdi.setvcm(600)
            except ImportError, e:
                print '  EderFtdi module NOT installed.'
                print '  EderFtdi module MUST BE installed for MB1.'

        self.rpi  = gpio.EderGpio(self.board_type)
        self.regs = register.Register(self.board_type)
        self.mems = memory.Memory(self.board_type)
        self.status = eder_status.EderStatus()
        if log_instance == None:
            self.logger = eder_logger.EderLogger()
        else:
            self.logger = log_instance
        #
        self.pll  = pll.Pll(eder_version)
        self.adc  = adc.Adc()
        #
        self.eeprom = eeprom.Eeprom(self.board_type)
        self.temp = temp.Temp()
        self.rx = rx.Rx(eder_version)
        self.tx = tx.Tx(eder_version)
        self.mode = None
        self.chip_present_status = False

        # Initialisation
        if init:
            self.init()            
        else:
            self.check()


        # Background daemons
        if backgr:
            self.com = self.background.BackgroundTask(5, self.bg_check)

        #self.chip_mon = self.background.BackgroundTask(300, self.chip_monitor)

    def init(self,do_print=False):
        self.reset()
        if self.check() == True:
            if self.regs.verify('default',do_print):
                self.pll.init()
                self.temp.init()
                self.status.set_mode(self.status.SX_MODE)
                self.logger.log_info('Chip init into SX mode.',2)
                return True
        return False

    def fpga_clk(self, mode):
        if (mode == 1):
            self.regs.wrrd('fast_clk_ctrl',0x02)
        else:
            self.regs.wrrd('fast_clk_ctrl',0x00)

    def reset(self, rst_time_in_ms=1):
        self.pll.reset()
        self.adc.reset()
        self.temp.reset()
	self.rx.reset()
	self.tx.reset()
        self.mode = None
        self.rpi.reset(rst_time_in_ms)
        self.logger.log_info('Chip reset.',2)

    def check(self):
        chip_id = self.regs.rd('chip_id')
        if self.chip_is_present():
            self.logger.log_info('Chip present (chip_id = 0x{:0{}X}).'.format(chip_id,8),2)
            return True
        else:
            self.logger.log_info('No chip present (chip_id = 0x{:0{}X})!'.format(chip_id,8),2)
            return False
        
    def bg_check(self):
        if self.chip_present_status == False:
            if self.chip_is_present():
                chip_id = self.regs.rd('chip_id')
                self.logger.log_info('Chip became present (chip_id = 0x{:0{}X})!'.format(chip_id,8),2)
            return True
        else:
            if self.chip_is_present() == False:
                chip_id = self.regs.rd('chip_id')
                self.logger.log_info('Chip disconnected (chip_id = 0x{:0{}X})!'.format(chip_id,8),2)
            return False
        
    def chip_is_present(self, chip_id_ref=0x02711702):
        chip_id = self.regs.rd('chip_id')
        if (chip_id == chip_id_ref):
            self.chip_present_status = True
            return True
        else:
            self.chip_present_status = False
            return False

    def mbist(self):
        self.reset();   
        self.init();      # Enable 45 MHz-clock to digital block. This is the clocl used for MBIST
        print 
        print '---------------------------------------------------------'
        print hex(self.mems.mbist.rd('bf_rx_mbist_done')) + ' (should be 0x0)'
        print hex(self.mems.mbist.rd('bf_tx_mbist_done')) + ' (should be 0x0)'
        print hex(self.mems.mbist.rd('bf_rx_mbist_result')) + ' (should be 0x0)'
        print hex(self.mems.mbist.rd('bf_tx_mbist_result')) + ' (should be 0x0)'
        self.mems.mbist.wr('bf_rx_mbist_en',0xFFFF)
        self.mems.mbist.wr('bf_tx_mbist_en',0xFFFF)
        print hex(self.mems.mbist.rd('bf_rx_mbist_done')) + ' (should be 0xffff)'
        print hex(self.mems.mbist.rd('bf_tx_mbist_done')) + ' (should be 0xffff)'
        print '*** MBIST Result ***'
        print '[RX] ' + hex(self.mems.mbist.rd('bf_rx_mbist_result')) + ' (should be 0x0)'
        print '[TX] ' + hex(self.mems.mbist.rd('bf_tx_mbist_result')) + ' (should be 0x0)'
        print '---------------------------------------------------------'
        print 
        self.reset();


    def chip_monitor(self):
        temperature = self.temp.run()
        self.logger.log_info(temperature)

    # RX
    def rx_setup(self, freq, pll_setup=True):
        if pll_setup:
            self.pll.init()
            self.pll.set(freq)
        self.rx.setup(freq)

    def rx_enable(self):
        self.rx.enable()
        self.mode = 'RX'

    def rx_disable(self):
        self.rx.disable()
        self.mode = None


    # TX
    def tx_setup(self, freq, pll_setup=True):
        if pll_setup:
            self.pll.init()
            self.pll.set(freq)
        self.tx.setup(freq)
        
        # Restore some registers from RFM EEPROM if valid
        rfm_id = self.get_rfm_id()
        if freq == 58.32e9:
            channel = 1
        elif freq == 60.48e9:
            channel = 2
        elif freq == 62.64e9:
            channel = 3
        elif freq == 64.8e9:
            channel = 4
        else:
            channel = 0

        if not self.restore_settings(channel):
            # Read from json file
            json_file_name = rfm_id + '.json'
            self.logger.log_info('Checking if settings-file "{0}" exists.'.format(json_file_name),2)
            try:
                tx_json_regs = json.read(json_file_name, print_error=False)
                self.logger.log_info('Reading ' + json_file_name,4)
                eder.regs.dump(tx_json_regs)
            except:
                self.logger.log_warning('No settings-file exist.',4)
                self.logger.log_info('Using normal setup.',2)

        self.logger.log_info('TX setup complete',2)

    def tx_enable(self):
        self.tx.enable()
        self.mode = 'TX'
		
    def tx_disable(self):
        self.tx.disable()
        self.mode = None
		

    # TRX
    def trx_setup(self, freq):
        self.pll.init()
        self.pll.set(freq)
        self.logger.log_info('PLL setup complete',2)
        self.tx_setup(freq, pll_setup=False)
        self.rx_setup(freq, pll_setup=False)

    def trx_enable(self, trx='tgl'):
        if trx == 'tgl':
            if self.mode == None:
                self.tx_disable()
                self.rx_enable()
            elif self.mode == 'RX':
                self.rx_disable()
                self.tx_enable()
            elif self.mode == 'TX':
                self.tx_disable()
                self.rx_enable()
        elif trx == 'rx':
            self.tx_disable()
            self.rx_enable()
        elif trx == 'tx':
            self.rx_disable()
            self.tx_enable()

    def trx_hw_sw_enable(self):
        self.tx.hw_sw_enable()
        self.rx.hw_sw_enable()
        
    def trx_hw_sw_disable(self):
	self.rpi.trx_mode_disable()
        self.tx.hw_sw_disable()
        self.rx.hw_sw_disable()



    # LOOP
    def loop_setup(self, freq):
		self.pll.init()
		self.pll.set(freq)
		self.tx.setup(freq)
		self.regs.wr('bias_ctrl_rx',0x14242)
		self.rx.setup(freq)
		self.regs.wr('bias_tx',0x97FE)
		self.regs.wr('tx_rf_gain',0xc)
		self.regs.wr('bias_ctrl_tx',0x14242)
		self.logger.log_info('Loop setup complete')
		self.regs.wr('tx_rx_sw_ctrl',0x06)
		self.regs.wr('tx_rf_gain',0x0F)

    def loopback_setup(self, freq):
        import rx
        import tx
        self.reset()
        self.pll.init()
        self.pll.set(freq)
        self.tx.setup(freq)
        self.rx.setup(freq)
        self.logger.log_info('Loopback setup complete')

    def loopback_enable(self):
        self.regs.wr('tx_rx_sw_ctrl',0b110)        # bit0=0 for TX or RX enable

    def loopback_disable(self):
        self.regs.wr('tx_rx_sw_ctrl', 0b000)

    def sx_enable(self):
        """Enter SX mode from TX or RX mode
           Example: eder.sx_enable()
        """
        self.rx_disable()
        self.tx_disable()
        self.tx_rx_hw_disable()

    def tx_rx_hw_enable(self):
        """Enables TX/RX mode switching using TX_RX_SW input
        Example: eder.tx_rx_hw_enable()
        """
        self.regs.set('tx_rx_sw_ctrl', 0b001)

    def tx_rx_hw_disable(self):
        """Disables TX/RX mode switching using TX_RX_SW input
        Example: eder.tx_rx_hw_enable()
        """
        self.regs.clr('tx_rx_sw_ctrl', 0b001)

    def get_rfm_id(self):
        if self.board_type == 'MB1':
            wait_time = 0.01
            rfm_id = ''
            # Check if EEPROM data is valid
            x = self.ederftdi.readeprom(0x80)
            if x!=0xab:
                print 'rfm id not valid!'
                return ''
            for addr in xrange(0x81,0x8A+1):
                x = self.ederftdi.readeprom(addr)
                if x!=0:
                    rfm_id += chr(x)
                elif x==0:
                    return rfm_id 
                time.sleep(wait_time)
        else:
            return '' 



    def store_settings(self, rfm_id, channel):
        if self.board_type == 'MB1':
            wait_time = 0.01
            if len(rfm_id) == 0:
                print 'rfm_id not specified'
                return False
            if channel<1 or channel>6:
                self.logger.log_warning('RFM EEPROM channel must be between 1 and 6.',4)
                return False
            # RFM EEPROM ID valid flag 0x80  set to 0xab
            self.ederftdi.writeeprom(0x80, 0xab)
            time.sleep(wait_time)

            # RFM EEPROM ID Addresses 0x81-0x8A
            for addr in xrange(0x81,0x8A+1):
                time.sleep(wait_time)
                if len(rfm_id) > addr-0x81:
                    self.ederftdi.writeeprom(addr, ord(rfm_id[addr-0x81]))
                else:
                    self.ederftdi.writeeprom(addr, 0)

            time.sleep(wait_time)
            # Channel data valid flag set to 0xab
            addr = 0x8B + (channel - 1) * 6
            self.ederftdi.writeeprom(addr, 0xa0 + channel)
            time.sleep(wait_time)

            # Calculate address for channel
            addr = 0x8B + (channel - 1) * 6
            time.sleep(wait_time)
            self.ederftdi.writeeprom(addr+1, self.regs.rd('tx_bb_i_dco'))
            time.sleep(wait_time)
            self.ederftdi.writeeprom(addr+2, self.regs.rd('tx_bb_q_dco'))
            time.sleep(wait_time)
            self.ederftdi.writeeprom(addr+3, self.regs.rd('tx_bb_phase'))
            time.sleep(wait_time)
            self.ederftdi.writeeprom(addr+4, self.regs.rd('tx_bb_iq_gain'))
            time.sleep(wait_time)
            self.ederftdi.writeeprom(addr+5, self.regs.rd('tx_bb_gain'))
            return True
        else:
            return False

    def restore_settings(self, channel):
        self.logger.log_info('Checking if RFM EEPROM is programmed with settings.',2)
        if self.board_type == 'MB1':
            wait_time = 0.01

            if channel<1 or channel>6:
                self.logger.log_warning('RFM EEPROM channel must be between 1 and 6.',4)
                return False

            # Channel data valid flag set to 0xab
            addr = 0x8B + (channel - 1) * 6
            valid_flag = self.ederftdi.readeprom(addr)
            time.sleep(wait_time)
            if valid_flag != (0xa0+channel):
                self.logger.log_info('RFM EEPROM not programmed.',4)
                return False
            
            # Calculate address for channel
            addr = 0x8B + (channel - 1) * 6
            self.regs.wr('tx_bb_i_dco', self.ederftdi.readeprom(addr+1))
            time.sleep(wait_time)
            self.regs.wr('tx_bb_q_dco', self.ederftdi.readeprom(addr+2))
            time.sleep(wait_time)
            self.regs.wr('tx_bb_phase', self.ederftdi.readeprom(addr+3))
            time.sleep(wait_time)
            self.regs.wr('tx_bb_iq_gain', self.ederftdi.readeprom(addr+4))
            time.sleep(wait_time)
            self.regs.wr('tx_bb_gain', self.ederftdi.readeprom(addr+5))
            return True
        else:
            return False

    def run_rx(self, freq=60.48e9):
        self.reset()
        self.tx_disable()
        if self.board_type == 'MB1':
            self.ederftdi.setvcm(700)
        self.rx_setup(freq)
        self.rx_enable()

    def run_tx(self, freq=60.48e9):
        self.reset()
        self.rx_disable()
        self.tx_setup(freq)
        self.tx_enable()
        self.regs.wrrd('tx_rf_gain',0x07)

    def rdwrtime(self, n):
        import time
        start_time = time.time()
        for i in xrange(0, n):
            self.regs.rd('chip_id_sw_en')
            self.regs.wr('chip_id_sw_en',0)
        elapsed_time = time.time() - start_time
        print elapsed_time * 1000

    def run_tx_lo_leakage_cal(self):
        #self.reset()
        if self.board_type == 'MB1':
            self.ederftdi.setvcm(600)
        self.init()
        self.pll.init()
        self.pll.set(60.48e9)
        self.tx_setup(0.0, pll_setup=False)
        self.rx.setup_no_dco_cal(0.0)
        self.regs.wr('bias_ctrl_rx',0x13FFC)
        self.regs.wr('bias_ctrl_tx',0x13FFC)
        self.regs.set('tx_rx_sw_ctrl', 0x06)
        self.tx.dco.run()
        tx_bb_i_dco = self.regs.rd('tx_bb_i_dco')
        tx_bb_q_dco = self.regs.rd('tx_bb_q_dco')
        self.rx.disable()
        self.tx.disable()
        self.reset()
        self.regs.wr('tx_bb_i_dco', tx_bb_i_dco)
        self.regs.wr('tx_bb_q_dco', tx_bb_q_dco)

    def tx_pdet_bias_meas(self):
        power = {}
        stored_tx_bb_ctrl = self.regs.rd('tx_bb_ctrl')
        self.regs.wr('tx_bb_ctrl', stored_tx_bb_ctrl&0xfc)
        for pdet_index in range(0x10, 0x20):
            self.adc.start(7)
            self.regs.wr('tx_bf_pdet_mux', pdet_index)
            power_det_value = self.adc.mean(self.adc.dump(16))
            self.adc.stop()
            power['TX'+str(pdet_index - 0x10)] = power_det_value
        self.pdet_bias = power
        self.regs.wr('tx_bb_ctrl', stored_tx_bb_ctrl)

    def tx_pdet(self):
        # Reference values
        # ADC values (offset subtracted) [3, 14, 19, 61, 108, 154, 243, 386, 527]
        # Power meter values (dBm) [-15.5, -8.98, -7.1, -2.5, 0.1, 1.66, 3.89, 6.04, 7.28]
        # slope (using first and last values) calculated power meter values in W :  98543.29382665164
        #f = lambda x: 1.0062851704772065e-05*x + 3.7902775851350427e-06
        pll_divn = self.regs.rd('pll_divn')
        if pll_divn == self.pll.freq_to_divn(60.48e9):
            print 'freq: ' + str(60.48e9)
            f = lambda x: (2.056e-06*x)-8.6514E-05
        elif pll_divn == self.pll.freq_to_divn(62.64e9):
            print 'freq: ' + str(62.64e9)
            f = lambda x: (2.262e-06*x)-1.92E-05
        elif pll_divn == self.pll.freq_to_divn(66.96e9):
            print 'freq: ' + str(66.96e9)
            f = lambda x: (2.160e-06*x)-2.39259E-05
        elif pll_divn == self.pll.freq_to_divn(69.12e9):
            print 'freq: ' + str(69.12e9)
            f = lambda x: (1.166e-06*x)-1.71265E-06
        elif pll_divn == self.pll.freq_to_divn(58.32e9):
            print 'freq: ' + str(58.32e9)
            f = lambda x: (2.7e-06*x)-0.000109332
        else:
            print 'Frequency not set'
            return

        power = {}
        bias_ctrl_tx = self.regs.rd('bias_ctrl_tx')
        if self.pdet_bias == None:
            self.tx_pdet_bias_meas()
        print self.pdet_bias
        for pdet_index in range(0x10, 0x20):
            self.adc.start(7)
            self.regs.wr('tx_bf_pdet_mux', pdet_index)
            power_det_value = self.adc.mean(self.adc.dump(16))
            self.adc.stop()
            print 'ADC TX' + str(pdet_index - 0x10) + ': ' + str(power_det_value)
            if self.pdet_bias['TX'+str(pdet_index - 0x10)] >= power_det_value:
                power['TX'+str(pdet_index - 0x10)] = f(0)
            else:
                power['TX'+str(pdet_index - 0x10)] = f(abs(power_det_value - self.pdet_bias['TX'+str(pdet_index - 0x10)]))
            if bias_ctrl_tx & (1 << (pdet_index - 0x10)):
                if power['TX'+str(pdet_index - 0x10)] > 0:
                    print 'power[TX' + str(pdet_index - 0x10) + '] = ' + str(power['TX'+str(pdet_index - 0x10)])
                    print 'TX' + str(pdet_index - 0x10) + ':' + str(round(30 + 10*math.log10(power['TX'+str(pdet_index - 0x10)]), 2)) + ' dBm'
        total_power = 0
        for i in range(0, 0x10):
            if bias_ctrl_tx & (1 << i):
                total_power = total_power + power['TX'+str(i)]
        if total_power <= 0:
            return None
        return round(30 + 10*math.log10(total_power), 2) # In dBm

    def load_test_module(self):
        import test
        self.test = test.Test(self)

    def vcm_check(self):
        measured_values = self.rx.dco.iq_meas.meas(meas_type='xx')
        time_stamp = self.common.get_time_stamp()
        with open(self.rxbb_vcm_to_csv_file_name, 'ab') as vcm_log:
            writer = self.csv.writer(vcm_log)
            measured_values['idiff'] = self.rx.dco._decToVolt(measured_values['idiff'])
            measured_values['qdiff'] = self.rx.dco._decToVolt(measured_values['qdiff'])
            measured_values['icm'] = self.rx.dco._decToVolt(measured_values['icm'])
            measured_values['qcm'] = self.rx.dco._decToVolt(measured_values['qcm'])
            writer.writerow([time_stamp, round(self.temp.run()-273, 2), measured_values['idiff'], measured_values['qdiff'], measured_values['icm'], measured_values['qcm']])
            vcm_log.close()

    def rxbb_vcm_to_csv(self, minutes=0.5, file_name='vcm_log.csv'):
        """Start logging of RX DC offset to file for a specified period of time (in minutes).
        Default file name: vcm_log.csv
        Default logging duration: 0.5 minutes
        Example: To log for 0.5 minutes to file vcm_log.csv
                 eder.rxbb_vcm_to_csv()
     
                 To log for 5 minutes to file vcm_log.csv
                 eder.rxbb_vcm_to_csv(5)

                 To log for 2 minutes to file vcm_log_2.csv
                 eder.rxbb_vcm_to_csv(2, 'vcm_log_2.csv')
        """
        self.rxbb_vcm_to_csv_file_name = file_name
        with open(file_name, 'ab') as vcm_log:
            writer = self.csv.writer(vcm_log)
            writer.writerow(["%Time", "Temp.", " V_i_diff", " V_q_diff", " V_i_com", " V_q_com"])
            vcm_log.close()
        self.vcm_mon = self.background.BackgroundTask(1, self.vcm_check)
        self.rxbb_vcm_timer = Timer(minutes*60, self.rxbb_vcm_stop)
        self.rxbb_vcm_timer.start()

    def rxbb_vcm_stop(self):
        self.vcm_mon.stop()


def cmd_hist_file(fname="eder.cmd"):
    import atexit
    import os
    import readline

    histfile = os.path.join(os.path.expanduser(""), fname)
    print '  Command history file: ' + histfile
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(-1)
    except IOError:
        pass

    log_header = '**** New session started on ' + time.asctime()
    readline.add_history(log_header)

    atexit.register(readline.write_history_file, histfile)

def info_file(fname="eder.info"):
    import eder_logger
    return eder_logger.EderLogger(fname)

def get_args():
    import argparse
    parser = argparse.ArgumentParser(description='Command line options.')
    parser.add_argument('--board', '-b', dest='board_type', choices=['MB0', 'MB1'], default='MB0',
                         help='Specify type of motherboard')
    parser.add_argument('--unit', '-u', dest='unit_name', metavar='UNIT', default=None,
                         help='Specify unit name')
    parser.add_argument('--ederver', '-v', dest='eder_ver', metavar='EDERVER', default='2',
                         help='Specify Eder generation')
    return parser.parse_args()
    
if __name__ == "__main__":
    args = get_args()
    info_logger=info_file()
    cmd_hist_file()
    import rlcompleter, readline
    readline.parse_and_bind('tab:complete')
    import fileHandler as json

    
    if args.board_type == 'MB0':
        info_logger.log_info('Connecting to device connected to motherboard {0}.'.format(args.board_type),2)
	eder = Eder(log_instance=info_logger, board_type='MB0', eder_version=args.eder_ver)
    elif args.board_type == 'MB1':
        try:
            info_logger.log_info("  Trying to import module ederftdi",2)
            import ederftdi
            if args.unit_name == None:
                ederftdi.listdevs()
                print("  Run again and select one of the above devices")
            else:
                print '  Connecting to device with unit name {0} connected to motherboard {1}.'.format(args.unit_name, args.board_type)
                print '  Using settings for Eder Gen {0}'.format(args.eder_ver)
                eder = Eder(log_instance=info_logger, unit_name=args.unit_name, board_type=args.board_type, eder_version=args.eder_ver)
        except ImportError as ie:
            info_logger.log_error("Error! " + str(ie),2)


