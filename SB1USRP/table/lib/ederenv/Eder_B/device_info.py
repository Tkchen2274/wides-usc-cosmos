# List of used attributes
# chip_type     : 'Eder B' or 'Eder B MMF'
# rfm_type      : 'rfm_3.0' or 'rfm_2.5'
# rx_power_mode : 'low' or 'normal'
# tx_power_mode : 'low' or 'normal'

class DeviceInfo(object):

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(DeviceInfo, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance
    
    def __init__(self):
        if self.__initialized:
            return
        self.__initialized = True
        import evk_logger
        self.device_info = {}
        self.logger = evk_logger.EvkLogger()

    def get_attrib(self, attribute=None):
        if attribute != None:
            try:
                value = self.device_info[attribute]
            except:
                value = None
            return value
        else:
            return self.device_info

    def set_attrib(self, attribute, value):
        self.logger.log_bold('{0}: {1}'.format(attribute, value), 2)
        self.device_info[attribute] = value
