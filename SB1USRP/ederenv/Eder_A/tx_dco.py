class TxDco(object):
    import time
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import temp
        import eder_status
        import eder_logger
        self.__initialized = True
        self.regs = register.Register()
        self.rx_iq_meas = rx_iq_meas.RxIQMeas()
        self.temp = temp.Temp()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        

    def run(self,iq='iq', do_print=False):
        meastype='bb'
        wait_time = 0.005

        import rx
        import tx
        tx = tx.Tx()
        rx = rx.Rx()
            
        # Store current gain settings
        bias_ctrl_tx_stored = self.regs.rd('bias_ctrl_tx')
        tx_bb_iq_gain_stored = self.regs.rd('tx_bb_iq_gain')
        tx_bb_gain_stored = self.regs.rd('tx_bb_gain')
        tx_bf_gain_stored = self.regs.rd('tx_bf_gain')
        tx_rf_gain_stored = self.regs.rd('tx_rf_gain')
        bias_ctrl_rx_stored = self.regs.rd('bias_ctrl_rx')
        bias_lo_stored = self.regs.rd('bias_lo')
        tx_beam_store = tx.bf.awv.get()
   
        rx_bb_i_vga_1_2_stored = self.regs.rd('rx_bb_i_vga_1_2')
        rx_bb_q_vga_1_2_stored = self.regs.rd('rx_bb_q_vga_1_2')
        rx_bb_i_vga_1db_stored = self.regs.rd('rx_bb_i_vga_1db')
        rx_bb_q_vga_1db_stored = self.regs.rd('rx_bb_q_vga_1db')
        rx_bf_rf_gain_stored = self.regs.rd('rx_bf_rf_gain')
        bias_ctrl_rx_stored = self.regs.rd('bias_ctrl_rx')
        rx_bb_test_ctrl_stored = self.regs.rd('rx_bb_test_ctrl')
        rx_bb_en_stored = self.regs.rd('rx_bb_en')
        bias_rx_stored = self.regs.rd('bias_rx')

        freq = tx.freq
        print 'freq: ' + str(tx.freq)
        import time
        time.sleep(10)
        current_temp = self.temp.run()
        previous_temp = 0
        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(3)
                current_temp = self.temp.run()
                print 'temp: {0} C'.format(round(current_temp-273.15,2))

        target_temp = (current_temp - 273.15) * 1.05
        
        tx.disable()
        rx.disable()
        self.regs.wr('bias_ctrl_rx',0x10180)
        tx.bf.awv.setup('lut/beambook/bf_tx_awv_' + tx.eder_version, 0.0, 0.0)
        tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx_' + tx.eder_version, 0.0)
        tx.set_beam(0)
        rx.setup_no_dco_cal(0.0, 0, 0x10180)
        self.regs.set('tx_rx_sw_ctrl', 0x06)

        import time
        print 'Wait for temperature stabilization'
        previous_temp = 0
        current_temp = self.temp.run()

        while (current_temp - previous_temp) > 0.1:
                previous_temp = current_temp
                time.sleep(1)
                current_temp = self.temp.run()
                print 'temp: {0} C'.format(round(current_temp-273.15,2))
                if current_temp-273.15 > target_temp:
                    break
        if current_temp-273.15 > target_temp:
            print 'Target temperature reached'
        else:
            print 'Temperature stabilized'
        
        # Calibration starts here
        self.regs.wr('bias_ctrl_tx', 0x10180)
        self.regs.wr('tx_bf_gain', 0x0F)
        self.regs.wr('tx_rf_gain', 0x0F)

        import numpy as np
        
        # OK
        self.regs.wr('bias_ctrl_rx', 0x10180)
        self.regs.wr('rx_bb_i_vga_1_2', 0x7F)
        self.regs.wr('rx_bb_q_vga_1_2', 0x7F)
        self.regs.wr('rx_bb_i_vga_1db', 0x07)
        self.regs.wr('rx_bb_q_vga_1db', 0x07)
        #self.regs.wr('rx_bf_rf_gain', 0x00)
        self.regs.wr('rx_bf_rf_gain', 0xEE)
        #self.regs.wr('rx_bf_rf_gain', 0xFF)

        rx.enable()
        self.regs.clr('bias_lo', 0x08)

        #STEP 1: create parameters for calibration
        errorTXmax = 0         # maximum allowed error
        lower_limit= 7.0
        currentE   = 100       # place holder for error value
        minVI      = 0         # goal value for I
        minVQ      = 0         # goal value for Q
        stepI      = 6         # optimization step for I
        stepQ      = 6         # optimization step for Q
        iteration  = 0         # current optimizer iteration
        if 0x37 == self.regs.rd('tx_bb_ctrl'):
                iq_swap = True
		currentI   = 0x5A - stepI
        	currentQ   = 0x5A - stepQ
        else:
                iq_swap = False
		currentI   = 0x30 - stepI
        	currentQ   = 0x30 - stepQ

        #STEP 2: perform RX-calibration and read RX DC-offset value
        rx.dco.report('bb')
        rx.dco.run()
        #rx.dco.report()
        current_temp = self.temp.run()
        print 'temp: ' + str(current_temp-273.15)
        print "RX DCO Ready"
        time.sleep(0.05)
        TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
        print TRASH
        minVI = TRASH['idiff']
        minVQ = TRASH['qdiff']

        minVI = 0
        minVQ = 0

        #STEP 3: enable TX and read current offset Error
        self.regs.set('bias_lo', 0x08)
        
        self.regs.wr('tx_bb_i_dco',currentI)
        self.regs.wr('tx_bb_q_dco',currentQ)

        TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
        print TRASH
        valI  = TRASH['idiff']
        valQ  = TRASH['qdiff']
        currentE = abs((valI-minVI) + 1j*(valQ-minVQ))

        print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE)
        errorTXmax = currentE / 10
        prev_i = 0
        prev_q = 0
        skip_second_stage = False

        #STEP 4: run the search using modified 2D Newton-Rhapson method
        while (currentE >= errorTXmax) and (currentE > lower_limit) :
            if currentE < 10:
                stepI = 1
                stepQ = 1
            else:
                stepI = 6
                stepQ = 6

            # get rxDCoI & rxDCoQ @ I+step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI+stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            errorIP = abs((valI-minVI) + 1j*(valQ-minVQ))

            # get rxDCoI & rxDCoQ @ I-step,Q and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI-stepI)
            self.regs.wrrd('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            errorIN = abs((valI-minVI) + 1j*(valQ-minVQ))

            # get rxDCoI & rxDCoQ @ I,Q+step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ+stepQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            errorQP = abs((valI-minVI) + 1j*(valQ-minVQ))

            # get rxDCoI & rxDCoQ @ I,Q-step and calculate the ERROR
            self.regs.wrrd('tx_bb_i_dco',currentI)
            self.regs.wrrd('tx_bb_q_dco',currentQ-stepQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            errorQN = abs((valI-minVI) + 1j*(valQ-minVQ))

            # calculate the gradients for N-R iteration
            if (errorIP == errorIN) or (errorQP == errorQN):
            	continue
            slopeIQ = 1.5/((errorIP-errorIN) + 1j*(errorQP-errorQN))
            if (np.real(slopeIQ) == 0) or (np.imag(slopeIQ) == 0):
            	continue
            slopeI  =  1/np.real(slopeIQ)
            slopeQ  = -1/np.imag(slopeIQ)

            # calculate next I values for N-R iteration
            currentI = currentI + round(-1*currentE/slopeI*0.85)
            if currentI   > 127:
                currentI = 0x28
            elif currentI <  0:
                currentI = 0x64

            # calculate next Q values for N-R iteration
            currentQ = currentQ + round(-1*currentE/slopeQ*0.85)
            if currentQ   > 127:
                currentQ = 0x28
            elif currentQ <  0:
                currentQ = 0x64

            # measure new ERROR
            self.regs.wr('tx_bb_i_dco',currentI)
            self.regs.wr('tx_bb_q_dco',currentQ)
            time.sleep(wait_time)
            TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
            valI  = TRASH['idiff']
            valQ  = TRASH['qdiff']
            currentE = abs((valI-minVI) + 1j*(valQ-minVQ))

            print 'tx_bb_i_dco: 0x{0:02X}  tx_bb_q_dco: 0x{1:02X}  error: {2}'.format(int(currentI), int(currentQ), currentE)

            # Check if we're on the same value
            if (currentI == prev_i) and (currentQ == prev_q):
                skip_second_stage = False
                break
            else:
                prev_i = currentI
                prev_q = currentQ

        best_tx_bb_i_dco = 0
        best_tx_bb_q_dco = 0
        if skip_second_stage == False:
            lowest_error = 100
            currentI = int(currentI)
            currentQ = int(currentQ)
            if iq_swap == False:
                initial_i = currentI - 5
                initial_q = currentQ - 5
                final_i = currentI + 4
                final_q = currentQ + 4
            else:
                initial_i = currentI - 10
                initial_q = currentQ - 5
                final_i = currentI + 2
                final_q = currentQ + 2

            if initial_i < 0:
                initial_i = 0
            if initial_q < 0:
                initial_q = 0
            if final_i > 0x7F:
                final_i = 0x7F
            if final_q > 0x7F:
                final_q = 0x7F
            for i in range(initial_i, final_i+1):
                for q in range(initial_q, final_q+1):
                    print '.',
                    self.regs.wr('tx_bb_i_dco', i)
                    self.regs.wr('tx_bb_q_dco', q)
                    time.sleep(wait_time)
                    TRASH = tx.dco.rx_iq_meas.meas(meas_type=meastype)
                    valI  = TRASH['idiff']
                    valQ  = TRASH['qdiff']
                    currentE = abs((valI-minVI) + 1j*(valQ-minVQ))
                    if currentE < lowest_error:
                        lowest_error = currentE
                        best_tx_bb_i_dco = i
                        best_tx_bb_q_dco = q

            print
            self.regs.wr('tx_bb_i_dco',best_tx_bb_i_dco)
            self.regs.wr('tx_bb_q_dco',best_tx_bb_q_dco)

        if ((best_tx_bb_i_dco == 0) or (best_tx_bb_q_dco == 0)) and (skip_second_stage == False):
            print 'TX LO leakage calibration failed'
        else:
            print 'TX LO leakage calibration complete.'
            print 'tx_bb_i_dco: ' + hex(self.regs.rd('tx_bb_i_dco'))
            print 'tx_bb_q_dco: ' + hex(self.regs.rd('tx_bb_q_dco'))

        #STEP 5: print final I & Q values, final ERROR and number of iterations
        rx.disable()
        tx.bf.awv.setup('lut/beambook/bf_tx_awv_' + tx.eder_version, freq, 0.0)
        tx.bf.idx.setup('lut/beambook/bf_tx_awv_idx_' + tx.eder_version, freq)

        # Write back stored gain settings
        rx.status.clr_init_bit(rx.status.RX_INIT)
        self.regs.wrrd('bias_ctrl_tx', bias_ctrl_tx_stored)
        self.regs.wrrd('tx_bb_iq_gain', tx_bb_iq_gain_stored)
        self.regs.wrrd('tx_bb_gain', tx_bb_gain_stored)
        self.regs.wrrd('tx_bf_gain', tx_bf_gain_stored)
        self.regs.wrrd('tx_rf_gain', tx_rf_gain_stored)
        self.regs.wrrd('bias_ctrl_rx', bias_ctrl_rx_stored)
        self.regs.wrrd('bias_lo', bias_lo_stored)
        self.regs.wrrd('rx_bb_i_vga_1_2', rx_bb_i_vga_1_2_stored)
        self.regs.wrrd('rx_bb_q_vga_1_2',rx_bb_q_vga_1_2_stored)
        self.regs.wrrd('rx_bb_i_vga_1db',rx_bb_i_vga_1db_stored)
        self.regs.wrrd('rx_bb_q_vga_1db',rx_bb_q_vga_1db_stored)
        self.regs.wrrd('rx_bf_rf_gain',rx_bf_rf_gain_stored)
        self.regs.wrrd('bias_ctrl_rx',bias_ctrl_rx_stored)
        self.regs.wrrd('rx_bb_test_ctrl',rx_bb_test_ctrl_stored)
        self.regs.wrrd('rx_bb_en',rx_bb_en_stored)
        self.regs.wrrd('bias_rx',bias_rx_stored)
        tx.set_beam(tx_beam_store)
        

        
