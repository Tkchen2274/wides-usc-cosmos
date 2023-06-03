class Temp(object):

    __instance = None

    adc_ref_volt = 1.1
    adc_max      = 4095
    adc_scale    = 3
    adc_num_samp = 256
    temp_k       = 4e-3

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Temp, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import adc
        import eder_status
        import eder_logger
        self.adc = adc.Adc();
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()

    def reset(self):
        self.status.clr_init_bit(self.status.TEMP_INIT)

    def init(self):
        self.adc.init()
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.status.set_init_bit(self.status.TEMP_INIT)
            self.logger.log_info('Chip TEMP init.',2)
        else:
            self.logger.log_info('Chip TEMP already initialized.',2)

    def run(self, num_samp=adc_num_samp):
        if self.status.init_bit_is_set(self.status.TEMP_INIT) == False:
            self.init()
        self.adc.start(3)
        conv_fact = self.adc_scale*self.adc_ref_volt/self.adc_max/self.temp_k
        temp = self.adc.mean(self.adc.dump(num_samp))*conv_fact
        self.adc.stop()
        return temp
