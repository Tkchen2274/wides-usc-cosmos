class Pll(object):
    import time

    __instance = None

    ref_freq=45e6               # XO reference frequency
    alc_th_v=1.26               # VCO amplitude threshold = 1.26V
    atc_hi_th_v=2.4             # High tune voltage threshold = 2.4V
    atc_lo_th_v=0.4             # Low tune voltage threshold = 0.4V   
    mfix=0                      # Chip version, mfix=1 means metl mask changes chip
    alc_th=102
    atc_hi_th=191
    atc_lo_th=34
    dac_ref=3.0
    a_freq=0
    vtune=0
    t=-273
    adc_ref_volt = 1.1
    adc_max      = 4095
    adc_scale    = 3
    adc_num_samp = 256
    temp_k       = 4e-3

    pll_en_divn = (1 << 0)
    pll_en_div2 = (1 << 1)
    pll_en_leak = (1 << 2)
    pll_en_ld   = (1 << 3)
    pll_en_chp  = (1 << 4)
    pll_en_pfd  = (1 << 5)

    def __new__(cls,eder_version=2):
        if cls.__instance is None:
            cls.__instance = super(Pll, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, eder_version=2):
        if self.__initialized:
            return
        self.__initialized = True
        import ref
        import vco
        import register
        import eder_status
        import eder_logger
        import temp
        import adc
        self.eder_version = eder_version
        self.adc = adc.Adc()
        self.temp  = temp.Temp()
        self.regs = register.Register()
        self.ref  = ref.Ref()
        self.vco  = vco.Vco()
        self._status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()

    def freq_to_divn(self, freq):
        return int(freq/6/self.ref_freq-36)

    def divn_to_freq(self, divn):
        return (divn+36)*6*self.ref_freq

    def reset(self):
        self._status.clr_init_bit(self._status.PLL_INIT)
        self.ref.reset()
        self.vco.reset()

    def init(self):
        #self.ref.init()
        self.vco.init()
        self.temp.init()
        if self._status.init_bit_is_set(self._status.PLL_INIT) == False:
            self.regs.set('bias_ctrl',0x1f)                                          # Enable BG and LDO:s
            self.regs.wr('bias_pll',0x17)                                            # Set PLL bias till nominal current
            self.regs.wr('bias_lo',0x02)                                             # Set nominal bias for X3
            #
            self.regs.wr('pll_ref_in_lvds_en',0x01)                                  # Set REF input to LVDS
            self.regs.wr('pll_en',0x3b)                                              # Enable the PLL
            self.regs.wr('pll_chp',0x03)                                             # Set charge pump current to 1mA
            #
            self.regs.wr('vco_alc_del',0x2d)                                         # 1 us
            self.regs.wr('vco_tune_loop_del',0x02BF20)                               # 4 ms
            self.regs.wr('vco_vtune_set_del',0x00AFC8)                               # 1 ms
            self.regs.wr('vco_vtune_unset_del',0x02BF20)                             # 4 ms
            self.regs.wr('vco_override_ctrl',0x1ff)                                  # Override the internal state maskin
            #
            # Test if chip = metal fix version
            self.regs.wr('vco_atc_hi_th', 105)                                       # Set high tune voltage threshold close to 2.4V
            self.regs.wr('vco_vtune',0x13)                                           # Tune set voltage = 1.1V
            self.regs.wr('vco_en',0x3c)                                              # Enable VCO including comparators
            self.regs.wr('pll_pfd',0x03)                                             # Set PFD to source current
            #if self.regs.rd('vco_tune_det_status') >= 8:                            # Check if vco_atc_hi_th=1, (Vtune>2.4V)
            if self.eder_version == 1:
                self.mfix=0                                                          # Eder P1a version
                version=' Eder P1A version.'                                         # Version
                self.regs.wr('bias_pll',0x37)                                        # Set PLL bias till high current (+30%)
                self.dac_ref=3.16                                                    # Set the DAC reference to 3.15V
            else:                                                                    # Eder Gen 2
                self.mfix=1                                                          # Eder metal fix version
                version=' Eder metal fix version.'                                   # Version
                self.regs.wr('bias_pll',0x17)                                        # Set PLL bias till nominal current
                self.dac_ref=2.82                                                        # Set the DAC reference to 3.0V
            self.regs.wr('vco_vtune',0x02)                                           # Tune set voltage disable
            # end version test
            #
            self.alc_th=int(self.alc_th_v/self.dac_ref*255)                          # VCO amplitude threshold
            self.atc_hi_th=int(self.atc_hi_th_v/self.dac_ref*255)                    # High tune voltage threshold
            self.atc_lo_th=int(self.atc_lo_th_v/self.dac_ref*255)                    # Low tune voltage threshold
            self.regs.wr('vco_atc_hi_th', self.atc_hi_th)                            # Set High tune voltage threshold
            self.regs.wr('vco_atc_lo_th',self.atc_lo_th)                             # Set Low tune voltage threshold
            #
            self.regs.wr('pll_pfd',0x00)                                             # Set PFD to normal operation
            self.regs.wr('vco_en',0x1c)                                              # Enable VCO
            self._status.set_init_bit(self._status.PLL_INIT)
            self.logger.log_info('Chip PLL init' + version,2)
        else:
            self.logger.log_info('Chip PLL already initialized.',2)


    def set(self, frequency):
        if self._status.init_bit_is_set(self._status.PLL_INIT) == False:
            self.init()
        self.regs.wr('vco_en',0x3c)                                                  # Enable the VCO including comparators
        if self.mfix == 0:                                                           # If P1A version disable the CHP
            self.regs.wr('pll_en',0x2b)                                              # Disable the Charge pump
            self.regs.wr('pll_ld_test_mux_in',0x01)           
            self.regs.wr('pll_ld_mux_ctrl',5)                                        # Set the LD output to 1
        else:
            self.regs.wr('pll_ld_mux_ctrl',0)                                        # Set LD mux to monitor lock detect
            self.regs.wr('pll_en',0x3b)                                              # Enable the PLL
        self.regs.wr('pll_divn',self.freq_to_divn(frequency))                        # Set PLL divider
        self.regs.wr('vco_override_ctrl',0x1ff)                                      # Override the internal state maskin
        self.tmp()                                                                   # Measure the temperature
        if self.t > 65:
            self.regs.wr('vco_vtune',0x11)                                           # Set tune voltage to 1.5V for temp over 65 degree
        else:
            if self.t < 10:
                self.regs.wr('vco_vtune',0x13)                                       # Set tune voltage to 1.1V for temp under 10 degree
            else:
                self.regs.wr('vco_vtune',0x12)                                       # Set tune voltage to 1.4V for temp 10 to 65 degree
        self.alc_th = int(((1.52-4.5e-3*self.t)*255)/self.dac_ref)                   # Calculate threshold for VCO amplitude
        self.regs.wr('vco_alc_hi_th',self.alc_th)                                    # Set threshold for VCO amplitude
        #
        atc = 32
        freq_tmp = 0
        atc_tmp = 64
        alc_tmp = 0
        for x in range(0,6,1):                                                        # VCO state maskin
            self.regs.wr('vco_ibias',0)                                               # Reset VCO amplitude
            self.regs.wr('vco_dig_tune',atc)                                          # Set VCO coarse tuning
            self.amp()                                                                # Set VCO amplitude
            self.time.sleep(0.01)
            self.f_cnt()                                                              # Frequency count
            self.time.sleep(0.01)
            #
            if abs(self.a_freq - 511) < abs(freq_tmp - 511):                          # Select closest frequency (previus or last state)
                freq_tmp = self.a_freq
                atc_tmp = atc
                alc_tmp = self.regs.rd('vco_ibias')
            #
            if self.a_freq <= 511:                                                    # Set the next stae for the SA depending on freq cnt
                atc = int(atc + 2**(4-x))
            else:
                atc = int(atc - 2**(4-x))
        #
        self.regs.wr('vco_ibias',0)                                                   # Reset VCO amplitude
        self.regs.wr('vco_dig_tune',atc_tmp)                                          # Set closest freq
        self.regs.wr('vco_ibias',alc_tmp)                                             # Set VCO amplitude
        self.regs.wr('pll_en',0x3b)                                                   # Enable the VCO
        self.regs.wr('vco_vtune',0x02)                                                # Release the tune voltage and let the PLL lock the frequency
        self.time.sleep(0.0015)
        status=self.regs.rd('vco_tune_det_status')
        if status&13 == 1:                                                            # Check that LD is high and tune voltage is within range
            self.logger.log_info('State maskin OK')
        else:
            self.stm2()
        #
        vco_amp = self.regs.rd('vco_ibias')              
        dig_tune = self.regs.rd('vco_dig_tune')
        self.logger.log_info('Ibias ' + str(vco_amp))                                             # VCO current setting
        self.logger.log_info('vco_dig_tune (bin) ' + bin(dig_tune))                               # VCO coarse tuning
        self.logger.log_info('Freq cnt ' + str(freq_tmp))                                         # CT frequency cnt
        self.logger.log_info('Detector status (bin) ' + bin(self.regs.rd('vco_tune_det_status'))) # Detector status
        m_div = self.regs.rd('pll_divn')
        self.logger.log_info('DIVN ' + str(m_div))                                                # VCO divider
        f_set=self.divn_to_freq(m_div)
        dig_tune_freq=freq_tmp/511.0*f_set
        self.logger.log_info('Set RF freq ' + str(f_set/1e9) + ' GHz')                            # RF freq
        self.logger.log_info('Dig tune freq error ' + str((dig_tune_freq-f_set)/1e6) + ' MHz')    # CT freq error
        self.monitor('Vtune')                                                                     # VCO amplitude
        self.monitor('VCOamp')                                                                    # VCO tune voltage
        self.regs.wr('vco_en',0x1c)                                                               # Turn off comparators

    def status(self, cnt):
        self.regs.wr('vco_en',0x3c)
        self.time.sleep(0.015)
        for i in xrange(0,cnt):
            self.logger.log_info(hex(self.regs.rd('vco_tune_status')))
        self.regs.wr('vco_en',0x1c)

    def monitor(self, sel_mon):
        if sel_mon == 'ld':                                                           # Monitor LD
            self.regs.wr('pll_ld_mux_ctrl',0x0)
            self.logger.log_info('Monitor LD')
        if sel_mon == 'ref':                                                          # Monitor reference frequency
            self.regs.wr('pll_ld_mux_ctrl',0x2)
            self.logger.log_info('Monitor REF freq dvided by 2')
        if sel_mon == 'vco':                                                          # Monitor VCO frequency
            self.regs.wr('pll_ld_mux_ctrl',0x3)
            m_div = self.regs.rd('pll_divn')
            self.logger.log_info('Monitor VCO freq divided by ' + str((m_div+36)*4))
        if sel_mon == 'test':                                                         # Monitor test output
            self.regs.wr('pll_ld_mux_ctrl',0x5)
        if sel_mon == 'Vtune':                                                        # Monitor tune voltage
            self.regs.wr('vco_en',0x3c)                                               # Turn on comparators
            dac = 128
            for x in range(0,8,1):                                                    # AD convert the tune voltage
                self.regs.wr('vco_atc_hi_th',dac)                                     # Set DAC value
                if self.regs.rd('vco_tune_det_status') >= 8:                          # Check if vco_atc_hi_th=1
                    dac = int(dac + 2**(6-x))                                         # Set next DAC vale for the SA
                else:
                    dac = int(dac - 2**(6-x))
            self.regs.wr('vco_atc_hi_th', self.atc_hi_th)                             # Set correct tune threshold
            self.logger.log_info('Vtune = ' + str(dac*self.dac_ref/255) + ' V')       # Write the tune voltage
            self.regs.wr('vco_en',0x1c)                                               # Turn off the comparators
        if sel_mon == 'VCOamp':                                                       # Monitor VCO amplitude
            self.regs.wr('vco_en',0x3c)                                               # Turn on comparators
            dac = 128
            for x in range(0,8,1):                                                    # AD convert the VCO amplitude
                self.regs.wr('vco_alc_hi_th',dac)                                     # Set DAC value
                alc=self.regs.rd('vco_tune_det_status')                               # Read detecor status
                if alc&2 >0:                                                          # Check if vco_alc_hi_th=1                                    
                    dac = int(dac + 2**(6-x))                                         # Set next DAC vale for the SA
                else:
                    dac = int(dac - 2**(6-x))
            self.regs.wr('vco_alc_hi_th',self.alc_th)                                 # Set correct VCO ampltude th
            self.logger.log_info('VCO amplitude = '+str(dac*self.dac_ref/255) + ' V') # Write the VCO amplitude
            self.regs.wr('vco_en',0x1c)                                               # Turn off the comparators
    
    def amp(self):                                                                    # Set the VCO amplitude
         for x in range(0,255,1):                                                     # Increase current until vco_alc_hi_th=1
             self.regs.wr('vco_ibias',x)
             alc=self.regs.rd('vco_tune_det_status')                                  # Read detector status
             if alc&2 >0:                                                             # Check if vco_alc_hi_th=1
                 break

    def f_cnt(self):                                                                  # Frequency count
         n = 4
         self.a_freq = 0
         for x in range(0,n,1):                                                       # Average freq. count
             self.regs.tgl('vco_tune_ctrl',0x01)
             self.time.sleep(0.015)
             self.a_freq = self.a_freq + self.regs.rd('vco_tune_freq_cnt')
         self.a_freq = self.a_freq/n*1.0
 
    def tmp(self, num_samp=adc_num_samp):                                             # Measure temp
         self.adc.start(3)
         conv_fact = self.adc_scale*self.adc_ref_volt/self.adc_max/self.temp_k
         self.t = self.adc.mean(self.adc.dump(num_samp))*conv_fact-273
         self.adc.stop()

    def stm2(self):                                                                   # Second VCO state maskin
        atc = 32
        self.tmp()                                                                    # Measure temp
        tune_v=1+(self.t+20)*0.8/120                                                  # Calculate target tune voltage
        tune_tmp = 0
        atc_tmp = 64
        alc_tmp = 0
        for x in range(0,6,1):                                                        # VCO state maskin
            self.regs.wr('vco_ibias',0)                                               # Reset VCO amplitude
            self.regs.wr('vco_dig_tune',atc)                                          # Set VCO coarse tuning
            self.amp()                                                                # Set VCO amplitude
            self.time.sleep(0.01)
            self.tune()
            #
            if abs(self.vtune - tune_v) < abs(tune_tmp - tune_v):                     # Select closest frequency (previus or last state)
                tune_tmp = self.vtune
                atc_tmp = atc
                alc_tmp = self.regs.rd('vco_ibias')
            #
            if self.vtune > tune_v:                                                   # Check if vco_atc_hi_th=1
                atc = int(atc + 2**(4-x))
            else:
                atc = int(atc - 2**(4-x))
            #
        self.regs.wr('vco_ibias',0)                                                   # Reset VCO amplitude
        self.regs.wr('vco_dig_tune',atc_tmp)                                          # Set closest freq
        self.regs.wr('vco_ibias',alc_tmp)                                             # Set VCO amplitude
        self.regs.wr('vco_atc_hi_th', self.atc_hi_th)                                 # High tune voltage threshold = 2.4V
        #
        status=self.regs.rd('vco_tune_det_status')
        if status&13 == 1:                                                            # Check that LD is high and tune voltage is within range
            self.logger.log_info('State maskin second try OK')

    def tune(self):                                                                  
         dac = 128
         for x in range(0,8,1):                                                       # AD convert the tune voltage
             self.regs.wr('vco_atc_hi_th',dac)                                        # Set DAC value
             if self.regs.rd('vco_tune_det_status') >= 8:                             # Check if vco_atc_hi_th=1
                 dac = int(dac + 2**(6-x))                                            # Set next DAC vale for the SA
             else:
                 dac = int(dac - 2**(6-x))
         self.regs.wr('vco_atc_hi_th', self.atc_hi_th)                                # Set correct tune threshold
         self.vtune = dac*self.dac_ref/255                                            # Save the tune voltage
         



     
 
    
 



