class RxDco(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(RxDco, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import rx_iq_meas
        import eder_status
        import eder_logger
        self.__initialized = True
        self.regs    = register.Register()
        self.iq_meas = rx_iq_meas.RxIQMeas()
        self.status  = eder_status.EderStatus()
        self.logger  = eder_logger.EderLogger()

    def init(self):
        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.iq_meas.init()
            self.status.set_init_bit(self.status.RXDCO_INIT)

    def default(self):
        self.regs.wr('rx_bb_q_dco',self.regs.value('rx_bb_q_dco'))
        self.regs.wr('rx_bb_i_dco',self.regs.value('rx_bb_i_dco'))

    def reset(self):
        self.default()
        self.iq_meas.reset()
        self.status.clr_init_bit(self.status.RXDCO_INIT)
    
    def _decToVolt(self, number):
        return round(0.00086954*number,6)

    def dco_split(self,dco_reg):
        return {'msb':dco_reg>>7, 'val':dco_reg&0x7f}
    
    def dco(self,msb,val):
            return (msb<<7) + val



    def print_report(self, meas):
        dco_i = self.regs.rd('rx_bb_i_dco')
        dco_q = self.regs.rd('rx_bb_q_dco')
        self.logger.log_info('rx_bb_i_dco : ' + hex(dco_i) + ' (' + hex(self.dco_split(dco_i)['msb']) + ',' + hex(self.dco_split(dco_i)['val']) + ')',2)
        self.logger.log_info('rx_bb_q_dco : ' + hex(dco_q) + ' (' + hex(self.dco_split(dco_q)['msb']) + ',' + hex(self.dco_split(dco_q)['val']) + ')',2)
        self.logger.log_info('V_i_diff    : ' + str(self._decToVolt(meas['idiff'])) + ' V',2)
        self.logger.log_info('V_q_diff    : ' + str(self._decToVolt(meas['qdiff'])) + ' V',2)
        self.logger.log_info('V_i_com     : ' + str(self._decToVolt(meas['icm'])) + ' V',2)
        self.logger.log_info('V_q_com     : ' + str(self._decToVolt(meas['qcm'])) + ' V',2)
        
        
    def report(self, meas_type='sys'):
        self.print_report(self.iq_meas.meas(16,meas_type))

        
    def sweep(self, meas_type='sys', search_scope='full', iq='iq', do_print=False):

        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.init()

        i       = {'min':100000000, 'dco':0, 'cal':0, 'msb':0}
        q       = {'min':100000000, 'dco':0, 'cal':0, 'msb':0}
        restore = {}

        restore['dco_i'] = self.regs.rd('rx_bb_i_dco')
        restore['dco_q'] = self.regs.rd('rx_bb_q_dco')
        
        self.report(meas_type)

        if search_scope == 'full':
		msb_scope = {0:(0,0), 1:(1,1), 2:(2,2), 3:(3,3)}
        else:
        	msb_scope = {0:search_scope}

        for k,(msb_i,msb_q) in msb_scope.iteritems():
            for y in xrange(0, 128):

                if (iq == 'iq') or (iq == 'q'):
                    self.regs.wr('rx_bb_q_dco',self.dco(msb_q,y))
                else:
                    self.regs.wr('rx_bb_q_dco',0)

                if (iq == 'iq') or (iq == 'i'):
                    self.regs.wr('rx_bb_i_dco',self.dco(msb_i,y))
                else:
                    self.regs.wr('rx_bb_i_dco',0)

                meas = self.iq_meas.meas_vdiff(16,meas_type,'No')

                if (abs(meas['idiff']) < i['min']):
                    i['min'] = abs(meas['idiff'])
                    i['dco'] = self.dco(msb_i,y)
                    i['msb'] = msb_i
                    i['cal'] = y
                if (abs(meas['qdiff']) < q['min']):
                    q['min'] = abs(meas['qdiff'])
                    q['dco'] = self.dco(msb_q,y)
                    q['msb'] = msb_q
                    q['cal'] = y
                if do_print:
                    self.report(meas_type)

        self.regs.wr('rx_bb_i_dco',restore['dco_i'])
        self.regs.wr('rx_bb_q_dco',restore['dco_q'])
        return {'q':q['dco'], 'i':i['dco'], 'imeas':i, 'qmeas':q}


    def run_dco_cal(self, iq, mtype='bb'):

        if iq == 'i':
            register = 'rx_bb_i_dco'
            diff = 'idiff'
        elif iq == 'q':
            register = 'rx_bb_q_dco'
            diff = 'qdiff'
        else:
            print 'Invalid argument.'
            return

        START = 0
        MID = 1
        END = 2

        rx_bb_dco = [0,0,0]
        dco_diff = [0,0,0]

        sign = lambda x: x and (1, -1)[x < 0]

        rx_bb_dco[START] = 0
        rx_bb_dco[END] = 511

        average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
        rx_bb_dco[MID] = int(round(average, 0))

        self.regs.wr(register, rx_bb_dco[START])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[START] = measured_values[diff]

        self.regs.wr(register, rx_bb_dco[MID])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[MID] = measured_values[diff]

        self.regs.wr(register, rx_bb_dco[END])
        measured_values = self.iq_meas.meas(meas_type=mtype)
        dco_diff[END] = measured_values[diff]

        while abs(rx_bb_dco[START]-rx_bb_dco[MID]) > 1:
            if sign(dco_diff[START]) == sign(dco_diff[MID]):
                rx_bb_dco[START] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[START] = dco_diff[MID]
                self.regs.wr(register, rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            elif sign(dco_diff[END]) == sign(dco_diff[MID]):
                rx_bb_dco[END] = rx_bb_dco[MID]
                average = (rx_bb_dco[START] + rx_bb_dco[END]) / 2
                rx_bb_dco[MID] = int(round(average, 0))
                dco_diff[END] = dco_diff[MID]
                self.regs.wr(register, rx_bb_dco[MID])
                measured_values = self.iq_meas.meas(meas_type=mtype)
                dco_diff[MID] = measured_values[diff]
            else:
                # mid_dco is 0'
                rx_bb_dco[START] = rx_bb_dco[MID]
            
        dco_diff = map(abs, dco_diff)
        i = dco_diff.index(min(dco_diff))
            
        self.regs.wr(register, rx_bb_dco[i])
        return rx_bb_dco[i]


    def run(self, meas_type='bb'):
        rx_bb_i_dco = self.run_dco_cal('i', meas_type)
        rx_bb_q_dco = self.run_dco_cal('q', meas_type)
        self.report(meas_type)
        return rx_bb_i_dco, rx_bb_q_dco

