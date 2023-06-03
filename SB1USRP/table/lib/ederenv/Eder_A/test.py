from cStringIO import StringIO
import sys


class Capturing_stdout(list):


    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

class Capturing_stderr(list):


    def __enter__(self):
        self._stderr = sys.stderr
        sys.stderr = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stderr = self._stderr

class Test(object):

    def __init__(self, eder):
	    self.eder = eder

    def run_all(self):
        self.check_spi()
        self.check_i2c()
        self.check_45mhz()
        self.mbist()

    def check_spi(self):
        if self.eder.check():
            print 'SPI check         [OK]'
            return True
        print 'SPI check         [FAIL]'
        return False

    def check_i2c(self):
        temp = self.eder.eeprom.read_pcb_temp()
        if temp > 0.0:
            print 'I2C check         [OK]'
            return True
        print 'I2C check         [FAIL]'
        return False

    def check_45mhz(self):
        temp = self.eder.temp.run()
        if temp > 0.0:
            print '45MHz clock check [OK]'
            return True
        print '45MHz clock check [FAIL]'
        return False

    def mbist(self, port):
        if (port != 0) and (port != 0):
            print 'Port must be 0 or 1'
            return NULL
        self.eder.reset()
        self.eder.init()
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all zeroes
        print bf_rx_mbist_done
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all zeroes
        print bf_tx_mbist_done
        result = (bf_rx_mbist_done == 0) and (bf_tx_mbist_done == 0)

        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print bf_rx_mbist_result
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print bf_tx_mbist_result
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.mems.mbist.wr('bf_rx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_tx_mbist_2p_sel', port)
        self.eder.mems.mbist.wr('bf_rx_mbist_en',0xFFFF)
        self.eder.mems.mbist.wr('bf_tx_mbist_en',0xFFFF)
        bf_rx_mbist_done = self.eder.mems.mbist.rd('bf_rx_mbist_done')  # Check that this is all ones
        print bf_rx_mbist_done
        bf_tx_mbist_done = self.eder.mems.mbist.rd('bf_tx_mbist_done')  # Check that this is all ones
        print bf_tx_mbist_done
        result = result and (bf_rx_mbist_done == 0xFFFF) and (bf_tx_mbist_done == 0xFFFF)

        bf_rx_mbist_result = self.eder.mems.mbist.rd('bf_rx_mbist_result')  # Check that this is all zeroes
        print bf_rx_mbist_result
        bf_tx_mbist_result = self.eder.mems.mbist.rd('bf_tx_mbist_result')  # Check that this is all zeroes
        print bf_tx_mbist_result
        result = result and (bf_rx_mbist_result == 0) and (bf_tx_mbist_result == 0)

        self.eder.reset()
        if result == True:
            print 'MBIST             [OK]'
            return True
        print 'MBIST RX:0x{0:04X} TX:0x{1:04X} [FAIL]'.format(bf_rx_mbist_result, bf_tx_mbist_result)
        return False



    # Internal AGC test

    def agc_test(self):
        import time

        self.eder.fpga_clk(1)

        self.eder.regs.wr('agc_en', 0x15)
        self.eder.regs.wr('agc_timeout', 200)
        self.eder.regs.wr('agc_use_agc_ctrls', 0x3F)
        self.eder.regs.wr('agc_detector_mask', 0x1F1F)
        self.eder.regs.wr('agc_bf_rf_gain_lvl', 0x55443322)
        self.eder.regs.wr('agc_bb_gain_1db_lvl', 0x654321)

        #self.eder.regs.wr('gpio_agc_done_ctrl', 0x02)

        self.eder.ederftdi.setagcrst(1)
        time.sleep(0.01)
        self.eder.ederftdi.setagcrst(0)

        self.eder.ederftdi.setagcstart(1)
        time.sleep(0.01)
        self.eder.ederftdi.setagcstart(0)

        agc_status = self.eder.ederftdi.getagcstate()
        while (agc_status & 0x80) == 0:
            agc_status = self.eder.ederftdi.getagcstate()

        print hex(self.eder.ederftdi.getagcstate())




    # ADC Measurement tests

    def dco_meas_error_debug(self, file_name='test_log.csv', num_samples=1, meas_type='bb', num_remeas=10, beam=0):
        '''
        Function used to debug strange ADC reaadings in the "trasselsudd" Eder package LO-leakage measurement.
        Remeasures the same beam setting num_remeas times.
        '''
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]", "Vtune", "VCOamp", "vco_det_tune_status"])
            dco_log.close()

        rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf1)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf1)
        self.eder.rx.dco.run()

        self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
        self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

        self.eder.rx.set_beam(beam)

        for i in xrange(num_remeas):
            time.sleep(0.1)
            self.dco_log(file_name, beam, num_samples, meas_type)

    def dco_beam_sweep_all_channels(self, device_sn='SN0000', num_samples=16, meas_type='bb'):
        import datetime
        import os
        import numpy as np
        from test import Capturing_stdout


        timenow = datetime.datetime.now()
        time_string = timenow.strftime('%y-%m-%d_%H_%M')
        # Does meas folder exist, otherwise create.
        dir_path = os.path.dirname(os.path.realpath(__file__)) + '/meas_data_dco/' + time_string + '/'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        center_freq = [58.32, 60.48, 62.64, 64.8, 66.69, 69.12]
        # Loop through all measurement frequencies
        for freq in center_freq:
            print "Running measurement for " + str(freq) + ' GHz'
            self.eder.run_rx(freq*1e9)
            #print "Eder vco_tune_det_status:"

            testfile_name = dir_path + device_sn + 'freq' + str(freq) + '.csv'
            self.dco_beam_sweep_extended(file_name=testfile_name, num_samples=num_samples, meas_type=meas_type)
            #regs_dump = self.eder.regs.dump(False)
            #np.save(testfile_name + '.npy', regs_dump)
            with Capturing_stdout() as output:
                self.eder.regs.dump()

            with open(testfile_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for item in output:
                    writer.writerow([item])
                dco_log.close()


    def dco_beam_sweep_extended(self, file_name='test_log.csv', num_samples=16, meas_type='bb'):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            #writer.writerow([meas_type, "", "", "", ""])
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]", "Vtune", "VCOamp", "vco_det_tune_status"])
            dco_log.close()
        # Read and store vga gain
        rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

        # Write new VGA gain and run DCO calibration
        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf1)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf1)
        self.eder.rx.dco.run()
        # Write back old vga gain values
        self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
        self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            self.dco_log_extended(file_name, beam, num_samples, meas_type)


    def dco_beam_sweep(self, file_name='test_log.csv', num_samples=16, meas_type='bb'):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            #writer.writerow([meas_type, "", "", "", ""])
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]"])
            dco_log.close()

        rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf1)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf1)
        self.eder.rx.dco.run()

        #self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
        #self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

        self.eder.regs.wr('rx_bb_i_vga_1_2', 0xf3)
        self.eder.regs.wr('rx_bb_q_vga_1_2', 0xf3)

        for beam in range(0,64):
            self.eder.rx.set_beam(beam)
            time.sleep(0.1)
            self.dco_log(file_name, beam, num_samples, meas_type)


    def dco_gain_beam_sweep(self, file_name='test_log.csv', num_samples=16, meas_type='bb', calib_bb_gain=0xf1):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            #writer.writerow([meas_type, "", "", "", ""])
            writer.writerow([meas_type])
            writer.writerow(["Beam", " Temp."," V_i_diff[ADC]"," V_i_diff[V]", " V_q_diff[ADC]", " V_q_diff[V]", " V_i_com[ADC]", " V_i_com[V]", " V_q_com[ADC]", " V_q_com[V]"])
            dco_log.close()

            vga_1_2_gain_vector = [0xFF, 0xF7, 0xF3, 0xF1, 0x71, 0x31, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                # 62.64e9
                writer.writerow([str(62.64) + ' ' + 'GHz'])
                dco_log.close()
                self.eder.run_rx(62.64e9)

                rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
                rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

                self.eder.regs.wr('rx_bb_i_vga_1_2', calib_bb_gain)
                self.eder.regs.wr('rx_bb_q_vga_1_2', calib_bb_gain)
                self.eder.rx.dco.run()

                self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
                self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

                for vga_gain in vga_1_2_gain_vector:
                    with open(file_name, 'ab') as dco_log:
                        writer = self.eder.csv.writer(dco_log)
                        writer.writerow(['vga_1_2_gain ' + hex(vga_gain)])
                        dco_log.close()
                    self.eder.regs.wr('rx_bb_i_vga_1_2', vga_gain)
                    self.eder.regs.wr('rx_bb_q_vga_1_2', vga_gain)
                    for beam in range(0,64):
                        self.eder.rx.set_beam(beam)
                        time.sleep(0.1)
                        self.dco_log(file_name, beam, num_samples, meas_type)

            self.eder.reset()

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                # 69.12e9
                writer.writerow([str(69.12) + ' ' + 'GHz'])
                dco_log.close()
                self.eder.run_rx(69.12e9)

                rx_bb_i_vga_1_2 = self.eder.regs.rd('rx_bb_i_vga_1_2')
                rx_bb_q_vga_1_2 = self.eder.regs.rd('rx_bb_q_vga_1_2')

                self.eder.regs.wr('rx_bb_i_vga_1_2', calib_bb_gain)
                self.eder.regs.wr('rx_bb_q_vga_1_2', calib_bb_gain)
                self.eder.rx.dco.run()

                self.eder.regs.wr('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2)
                self.eder.regs.wr('rx_bb_q_vga_1_2', rx_bb_q_vga_1_2)

                for vga_gain in vga_1_2_gain_vector:
                    with open(file_name, 'ab') as dco_log:
                        writer = self.eder.csv.writer(dco_log)
                        writer.writerow(['vga_1_2_gain ' + hex(vga_gain)])
                        dco_log.close()
                    self.eder.regs.wr('rx_bb_i_vga_1_2', vga_gain)
                    self.eder.regs.wr('rx_bb_q_vga_1_2', vga_gain)
                    for beam in range(0,64):
                        self.eder.rx.set_beam(beam)
                        time.sleep(0.1)
                        self.dco_log(file_name, beam, num_samples, meas_type)

    def dco_log(self, file_name, beam, num_samples, meas_type):
        measured_values = self.eder.rx.dco.iq_meas.meas(num_samples, meas_type)
        measured_values_v = dict()
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            temperature = round(self.eder.temp.run()-273, 1)
            measured_values_v['idiff'] = self.eder.rx.dco._decToVolt(measured_values['idiff'])
            measured_values_v['qdiff'] = self.eder.rx.dco._decToVolt(measured_values['qdiff'])
            measured_values_v['icm'] = self.eder.rx.dco._decToVolt(measured_values['icm'])
            measured_values_v['qcm'] = self.eder.rx.dco._decToVolt(measured_values['qcm'])
            writer.writerow([beam, temperature, measured_values['idiff'], measured_values_v['idiff'], measured_values['qdiff'],
                             measured_values_v['qdiff'], measured_values['icm'], measured_values_v['icm'], measured_values['qcm'], measured_values_v['qcm']])
            dco_log.close()

    def dco_log_extended(self, file_name, beam, num_samples, meas_type):

        measured_values = self.eder.rx.dco.iq_meas.meas(num_samples, meas_type)
        measured_values_v = dict()
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            temperature = round(self.eder.temp.run()-273, 1)
            measured_values_v['idiff'] = self.eder.rx.dco._decToVolt(measured_values['idiff'])
            measured_values_v['qdiff'] = self.eder.rx.dco._decToVolt(measured_values['qdiff'])
            measured_values_v['icm'] = self.eder.rx.dco._decToVolt(measured_values['icm'])
            measured_values_v['qcm'] = self.eder.rx.dco._decToVolt(measured_values['qcm'])
            # Read lock detect
            vco_tune_det_status = self.eder.regs.rd('vco_tune_det_status')
            # Read VCO tune voltage
            v_tune = self.eder.pll.monitor('Vtune', return_float=True)
            # Read VCO amplitude
            vco_amp = self.eder.pll.monitor('VCOamp', return_float=True)

            writer.writerow([beam, temperature, measured_values['idiff'], measured_values_v['idiff'], measured_values['qdiff'],
                             measured_values_v['qdiff'], measured_values['icm'], measured_values_v['icm'], measured_values['qcm'], measured_values_v['qcm'], v_tune, vco_amp, vco_tune_det_status])
            dco_log.close()


