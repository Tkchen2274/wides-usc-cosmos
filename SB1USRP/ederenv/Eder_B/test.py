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



    def dco_beam_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]
            beam_vector = [0, 14, 28, 32, 36, 50, 63]

            for beam_index in range(0,7):
                self.eder.rx.set_beam(beam_vector[beam_index])
                with open(file_name, 'ab') as dco_log:
                    writer = self.eder.csv.writer(dco_log)
                    writer.writerow(['beam', beam_vector[beam_index]])
                    for bb_gain_index in range(0,7):  
                        self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                        self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                        time.sleep(0.1)
                        trx_rx_on = self.eder.regs.rd('trx_rx_on')
                        self.eder.regs.wr('trx_rx_on', 0x1F0000)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                        self.eder.regs.wr('trx_rx_on', trx_rx_on)
                        writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()



    def dco_gain_sweep(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    time.sleep(0.1)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff'])])

            dco_log.close()
            self.eder.reset()

    def dco_gain_sweep_calib(self, file_name='test_log.csv', numsamples=16):
        import time
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(["BB1", "BB2", "i_diff[ADC]", " q_diff[ADC]", "i_diff[V]", " q_diff[V]", "rx_bb_i_dco", "rx_bb_q_dco"])
            dco_log.close()

            bb1_gain_vector = [0xFF, 0xFF, 0xFF, 0xFF, 0x77, 0x33, 0x11]
            bb2_gain_vector = [0xFF, 0x77, 0x33, 0x11, 0x11, 0x11, 0x11]

            with open(file_name, 'ab') as dco_log:
                writer = self.eder.csv.writer(dco_log)
                for bb_gain_index in range(0,7):  
                    self.eder.regs.wr('rx_gain_ctrl_bb1', bb1_gain_vector[bb_gain_index])
                    self.eder.regs.wr('rx_gain_ctrl_bb2', bb2_gain_vector[bb_gain_index])
                    rx_bb_i_dco, rx_bb_q_dco = self.eder.rx.dco.run()
                    time.sleep(0.5)
                    diff = self.eder.rx.dco.iq_meas.meas_vdiff(num_samples=numsamples)
                    writer.writerow([bb1_gain_vector[bb_gain_index], bb2_gain_vector[bb_gain_index], diff['idiff'], diff['qdiff'], self._AdcToVolt(diff['idiff']), self._AdcToVolt(diff['qdiff']), rx_bb_i_dco, rx_bb_q_dco])

            dco_log.close()
            self.eder.reset()

   
    def _AdcToVolt(self, number):
        #return round(0.0004815409309791332*number,6)
        #return round(0.0006015409309791332*number,6)
        return round(0.000886948*number,6)


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


    def dco_sweep(self, file_name='dco_sweep.csv', num_samples=16):
        with open(file_name, 'ab') as dco_log:
            writer = self.eder.csv.writer(dco_log)
            writer.writerow(['Shift', 'Mult. factor', 'Offset', 'i_diff', 'q_diff'])
            
            for shift in range(0,3):
                if shift == 0:
                    log_shift = 'no'
                elif shift == 1:
                    log_shift = 'neg.'
                else:
                    log_shift = 'pos.'
                for mult_fact in range(0,4):
                    if mult_fact == 0:
                        log_mult_fact = 'x1'
                    elif mult_fact == 1:
                        log_mult_fact = 'x2'
                    elif mult_fact == 2:
                        log_mult_fact = 'x3'
                    else:
                        log_mult_fact = 'x4'
                    for dco_reg_value in range(0,0x80):
                        rx_bb_iq_dco = dco_reg_value + (shift << 8) + (mult_fact << 12)
                        #print hex(rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_i_dco', rx_bb_iq_dco)
                        self.eder.regs.wr('rx_bb_q_dco', rx_bb_iq_dco)
                        diff = self.eder.rx.dco.iq_meas.meas_vdiff(meas_cm='Yes')
                        writer.writerow([log_shift, log_mult_fact, dco_reg_value, diff['idiff'], diff['qdiff']])
        dco_log.close()
        

