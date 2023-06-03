class TxDcoPowDet(object):
    import time
    import numpy as np
    #import matplotlib.pyplot as plt
    #import matplotlib.cm as cm
    from mpl_toolkits.mplot3d import axes3d
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(TxDcoPowDet, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        import register
        import amux
        import adc
        import pll
        import eder_status
        import eder_logger
        self.__initialized = True
        self.regs = register.Register()
        self.adc  = adc.Adc()
        self.pll  = pll.Pll()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.amux = amux.Amux(self.regs)
        
    def init_rx(self):
        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.pll.init()
            self.adc.init()
            self.status.set_init_bit(self.status.RXDCO_INIT)

    def reset(self):
        self.status.clr_init_bit(self.status.RXDCO_INIT)
        self.pll.reset()
        self.adc.reset()
    
    def sweep(self, channel, do_print=False):
        def dco(val):
            return val

        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.init()
        # Set Tx Power Detector bit.
        # This does the same as self.adc.start(self.amux.amux_tx_pd).
        self.amux.set(self.amux.amux_tx_pd) #87 hex
        self.regs.set('adc_ctrl',0x01)


        # Choose channel on tx_bf_ctrl to input.
        # tx_bf_ctrl = self.regs.rd("tx_bf_ctrl").
        self.regs.wr("tx_bf_pdet_mux", 0x1000|channel)
        # Choose same channel in bias_ctrl_tx.
        # Here each channel is chosen via per bit instead of multiplexer
        pos = 0 if channel == 0 else 1 << (channel-1)
        self.regs.wr("bias_ctrl_tx", 0x10000|pos)
        
        minValueFound = float("inf")
        values = [[0 for i in range(0,128)]for j in range(0,128)]
        iSet,qSet = self.regs.rd('tx_bb_i_dco'),self.regs.rd('tx_bb_q_dco')
        qrange = irange = range(0,128)
        for y in qrange:
            self.regs.wr('tx_bb_q_dco',dco(y))
            for k in irange:
                self.regs.wr('tx_bb_i_dco',dco(k))
                #self.time.sleep(0.1)
                #meas = self.meas()

                # Measure the TX
                measured = self.adc.mean(self.adc.dump(16))
                values[y][k] = measured
                #print measured
                # If found measurement is less than current min, replace settings
                if measured < minValueFound:
                    iSet = k
                    qSet = y
                    minValueFound = measured
                if do_print:
                    self.logger.log_info(str(y) + " : " + hex(y) + " : " + str(k) + " : " + hex(k))
                    self.logger.log_info("Measured Value : " + measured + " Smallest Value Found : " + minValueFound)
                
                #if do_print:
                #    self.logger.log_info(str(y) + ' : ' + hex(dco(y)) + ' ' + hex(self.regs.rd('tx_bb_i_dco')) + ' ' + hex(self.regs.rd('tx_bb_q_dco'))+ ' ' + str(meas['idiff']) + ' ' + str(meas['qdiff']))
                #    self.logger.log_info('   V_com       : ' + str(self._decToVolt(meas['cm']))    + ' V ( ' + str(meas['cm']) + ' )')
        # Disable amux and adc
        self.amux.clr()
        self.adc.stop()
        x = range(0,128)
        y = range(0,128)
       # z = self.np.reshape(values, (128,128))
        #fig = self.plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #X, Y = self.np.meshgrid(qrange,irange)
        #ax.plot_surface(X,Y,z)
        #ax.set_xlabel('q')
        #ax.set_ylabel('i')
        #ax.set_zlabel('mes')
        #print "DONE"
        #self.plt.show()

        return {'q':qSet, 'i':iSet}
        
    def run(self, channel=0, do_print=False):
        if self.status.init_bit_is_set(self.status.RXDCO_INIT) == False:
            self.init()
        dco = self.sweep(channel, do_print)
        self.regs.wr('tx_bb_q_dco',dco['q'])
        self.regs.wr('tx_bb_i_dco',dco['i'])
        
if __name__ == "__main__":
    import rlcompleter, readline, eder
    eder = eder.Eder()
    eder.reset()
    eder.init()
    eder.tx_setup(60.48e9)
    eder.tx_enable()
    readline.parse_and_bind('tab:complete')
    eder.tx.pdetdco.init_rx()
    eder.tx.pdetdco.run(2)
    eder.tx.disable()
    eder.reset()
    
