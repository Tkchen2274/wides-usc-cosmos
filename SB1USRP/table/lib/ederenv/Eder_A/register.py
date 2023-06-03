import ederspi


class Register(object, ederspi.EderSpi):

    __instance = None

    regs = {'chip_id':              {'addr':0x0000, 'size':4, 'value':0x02711702, 'mask':0xFFFFFFFF}, 
            'chip_id_sw_en':        {'addr':0x0004, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_rx_sw_ctrl':        {'addr':0x0005, 'size':1, 'value':0x00, 'mask':0xFF},
            'fast_clk_ctrl':        {'addr':0x0006, 'size':1, 'value':0x00, 'mask':0xFF},
            'gpio_tx_rx_sw_ctrl':   {'addr':0x0008, 'size':1, 'value':0x00, 'mask':0xEF},
            'gpio_agc_rst_ctrl':    {'addr':0x0009, 'size':1, 'value':0x00, 'mask':0xEF},
            'gpio_agc_start_ctrl':  {'addr':0x000a, 'size':1, 'value':0x00, 'mask':0xEF},
            'gpio_agc_done_ctrl':   {'addr':0x000b, 'size':1, 'value':0x02, 'mask':0xEF},
            'bist_amux_ctrl':       {'addr':0x000c, 'size':1, 'value':0x00, 'mask':0xFF},
            'bist_bgtest_ctrl':     {'addr':0x000d, 'size':1, 'value':0x00, 'mask':0xFF},
            'bist_ot_ctrl':         {'addr':0x000e, 'size':1, 'value':0x00, 'mask':0xFF},
            'bist_ot_temp':         {'addr':0x000f, 'size':1, 'value':0x80, 'mask':0x7F},
            'bist_ot_rx_off_mask':  {'addr':0x0011, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'bist_ot_tx_off_mask':  {'addr':0x0015, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            #
            'bias_ctrl':            {'addr':0x0020, 'size':1, 'value':0x00, 'mask':0xFF},
            'bias_ctrl_rx':         {'addr':0x0025, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'bias_ctrl_tx':         {'addr':0x0029, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'bias_off_ctrl_rx':     {'addr':0x002D, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'bias_off_ctrl_tx':     {'addr':0x0031, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'bias_vco_x3':          {'addr':0x0034, 'size':1, 'value':0x00, 'mask':0xFF},
            'bias_pll':             {'addr':0x0035, 'size':1, 'value':0x00, 'mask':0xFF},
            'bias_lo':              {'addr':0x0036, 'size':1, 'value':0x00, 'mask':0xFF},
            'bias_tx':              {'addr':0x0038, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'bias_rx':              {'addr':0x003a, 'size':2, 'value':0x00, 'mask':0xFF},
            #
            'pll_en':               {'addr':0x0040, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_divn':             {'addr':0x0041, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_pfd':              {'addr':0x0042, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_chp':              {'addr':0x0043, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_ld_mux_ctrl':      {'addr':0x0044, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_ld_test_mux_in':   {'addr':0x0045, 'size':1, 'value':0x00, 'mask':0xFF},
            'pll_ref_in_lvds_en':   {'addr':0x0046, 'size':1, 'value':0x00, 'mask':0xFF},
            #
            'tx_bb_ctrl':           {'addr':0x0060, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bb_q_dco':          {'addr':0x0061, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bb_i_dco':          {'addr':0x0062, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bb_phase':          {'addr':0x0063, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bb_gain':           {'addr':0x0064, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bb_iq_gain':        {'addr':0x0065, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_rf_gain':           {'addr':0x0066, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bf_gain':           {'addr':0x0067, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_bf_pdet_mux':       {'addr':0x0068, 'size':1, 'value':0x00, 'mask':0xFF},
            'tx_rf_mix_dc_lvl':     {'addr':0x0069, 'size':1, 'value':0x00, 'mask':0xFF},
            #
            'adc_ctrl':             {'addr':0x0080, 'size':1, 'value':0x00, 'mask':0xFF},
            'adc_clk_div':          {'addr':0x0081, 'size':1, 'value':0x00, 'mask':0xFF},
            'adc_sample_cycle':     {'addr':0x0082, 'size':1, 'value':0x00, 'mask':0xFF},
            'adc_sample':           {'addr':0x0090, 'size':16, 'value':0x0, 'mask':0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF},
            #
            'vco_en':               {'addr':0x00A0, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_dig_tune':         {'addr':0x00A1, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_ibias':            {'addr':0x00A2, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_vtune':            {'addr':0x00A3, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_atc_hi_th':        {'addr':0x00A4, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_atc_lo_th':        {'addr':0x00A5, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_alc_hi_th':        {'addr':0x00A6, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_amux_ctrl':        {'addr':0x00A7, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_tune_ctrl':        {'addr':0x00A8, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_alc_del':          {'addr':0x00A9, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_override_ctrl':    {'addr':0x00AA, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'vco_tune_loop_del':    {'addr':0x00AD, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'vco_vtune_set_del':    {'addr':0x00B1, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'vco_vtune_unset_del':  {'addr':0x00B5, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'vco_tune_status':      {'addr':0x00B8, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_tune_det_status':  {'addr':0x00B9, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_tune_freq_cnt':    {'addr':0x00BA, 'size':2, 'value':0x01FF, 'mask':0xFFFF},
            'vco_tune_dig_tune':    {'addr':0x00BC, 'size':1, 'value':0x20, 'mask':0xFF},
            'vco_tune_ibias':       {'addr':0x00BD, 'size':1, 'value':0x00, 'mask':0xFF},
            'vco_tune_fd_polarity': {'addr':0x00BE, 'size':1, 'value':0x01, 'mask':0xFF},
            #
            'rx_bf_rf_gain':        {'addr':0x00C0, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_en':             {'addr':0x00C1, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_biastrim':       {'addr':0x00C2, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_q_vga_1_2':      {'addr':0x00C4, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_q_vga_1db':      {'addr':0x00C5, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_i_vga_1_2':      {'addr':0x00C6, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_i_vga_1db':      {'addr':0x00C7, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_q_dco':          {'addr':0x00C8, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'rx_bb_i_dco':          {'addr':0x00CA, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'rx_bb_test_ctrl':      {'addr':0x00CC, 'size':1, 'value':0x00, 'mask':0xFF},
            'rx_bb_pdet_th':        {'addr':0x00D3, 'size':5, 'value':0x00, 'mask':0xFFFFFFFFFF},
            #
            'agc_en':               {'addr':0x00E0, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_start_delay':      {'addr':0x00E1, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_timeout':          {'addr':0x00E2, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_gain_change_delay':{'addr':0x00E3, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_detector_mask':    {'addr':0x00E4, 'size':2, 'value':0x1F1F, 'mask':0xFFFF},
            'agc_use_agc_ctrls':    {'addr':0x00E6, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_ctrl':             {'addr':0x00E7, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_bf_rf_gain_lvl':   {'addr':0x00E9, 'size':4, 'value':0x00, 'mask':0xFFFFFFFF},
            'agc_bb_gain_1db_lvl':  {'addr':0x00ED, 'size':3, 'value':0x00, 'mask':0xFFFFFF},
            'agc_status_detectors': {'addr':0x00F0, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'agc_status':           {'addr':0x00F2, 'size':1, 'value':0x00, 'mask':0xFF},
            'agc_gain_db':          {'addr':0x00F3, 'size':1, 'value':0xF4, 'mask':0xFF},
            'agc_backoff_db':       {'addr':0x00F4, 'size':2, 'value':0x00, 'mask':0xFFFF},
            'agc_gain_bits':        {'addr':0x00FB, 'size':5, 'value':0x00, 'mask':0xFFFFFFFFFF},
           }

    def __new__(cls, board_type='MB1'):
        if cls.__instance is None:
            cls.__instance = super(Register, cls).__new__(cls)
            cls.__instance.__initialized = False
        return cls.__instance

    def __init__(self, board_type='MB1'):
        if self.__initialized:
            return
        self.__initialized = True
        ederspi.EderSpi.__init__(self, self.regs, board_type)

