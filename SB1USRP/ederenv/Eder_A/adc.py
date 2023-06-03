from threading import Lock
class Adc(object):
    import time

    __instance = None
    __src_1 = None
    __src_2 = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Adc, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import register
        import ref
        import amux
        import eder_status
        import eder_logger
        self.regs   = register.Register()
        self.status = eder_status.EderStatus()
        self.logger = eder_logger.EderLogger()
        self.ref    = ref.Ref()
        self.amux   = amux.Amux(self.regs)
        self.lock = Lock()

    def reset(self):
        self.status.clr_init_bit(self.status.ADC_INIT)
        self.ref.reset()

    def init(self,div=23,cycle=10,set_edge=0):
        self.ref.init()
        self.regs.wr('adc_clk_div',div)
        self.regs.wr('adc_sample_cycle',cycle)
        self.edge(set_edge)
        self.status.set_init_bit(self.status.ADC_INIT)
        self.logger.log_info('Chip ADC init.',2)

    def edge(self,set_edge):
        if (set_edge == 1):
            self.regs.set('adc_ctrl',2)
        else:
            self.regs.clr('adc_ctrl',2)


    def start(self,src1, src2=None):
        self.lock.acquire()
        self.__src_1, self.__src_2 = self.amux.get()
        self.amux.set(src1,src2)
        self.regs.set('adc_ctrl',0x01)


    def stop(self):
        self.regs.clr('adc_ctrl',0x01)
        self.amux.set(self.__src_1,self.__src_2)
        self.lock.release()

    def dump(self,nos):
        adc_vals = []
        for num_of_samples in xrange(nos/8):
            self.time.sleep(0.01)
            try:
                adc_vals.extend(self.regs.rd('adc_sample',None,2))
            except:
                print 'Read register failed in adc.dump'
                return 0
        return adc_vals


    def mean(self,values):
        return reduce(lambda x, y: x + y, values)/len(values)

    def max(self,values):
        return max(values)

    def min(self,values):
        return min(values)

