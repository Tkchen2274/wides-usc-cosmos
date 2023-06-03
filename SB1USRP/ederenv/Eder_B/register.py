import ederspi


class Register(object, ederspi.EderSpi):

    __instance = None

    regs =   {'chip_id':                 {'addr':0x0000, 'size':4, 'value':0x02731803, 'mask':0xFFFFFFFF}, 
              'chip_id_sw_en':           {'addr':0x0004, 'size':1, 'value':0x00, 'mask':0x01},
              'fast_clk_ctrl':           {'addr':0x0005, 'size':1, 'value':0x00, 'mask':0x33},
              'gpio_tx_rx_sw_ctrl':      {'addr':0x0006, 'size':1, 'value':0x00, 'mask':0x13},
              'gpio_agc_rst_ctrl':       {'addr':0x0007, 'size':1, 'value':0x00, 'mask':0x13},
              'gpio_agc_start_ctrl':     {'addr':0x0008, 'size':1, 'value':0x00, 'mask':0x13},
              'gpio_agc_gain_in_ctrl':   {'addr':0x0009, 'size':1, 'value':0x00, 'mask':0xFF},
              'gpio_agc_gain_out_ctrl':  {'addr':0x000a, 'size':1, 'value':0x00, 'mask':0xFF},
              'bist_amux_ctrl':          {'addr':0x000b, 'size':1, 'value':0x00, 'mask':0xCF},
              'bist_ot_ctrl':            {'addr':0x000d, 'size':1, 'value':0x00, 'mask':0x33},
              'bist_ot_temp':            {'addr':0x000e, 'size':1, 'value':0x80, 'mask':0xDF},
              'bist_ot_rx_off_mask':     {'addr':0x000f, 'size':3, 'value':0x000000, 'mask':0x1FFFFF},
              'bist_ot_tx_off_mask':     {'addr':0x0012, 'size':3, 'value':0x000000, 'mask':0x1FFFFF},
              'spare':                   {'addr':0x001C, 'size':4, 'value':0xFF0000FF, 'mask':0xFFFFFFFF},
              #
              'bias_ctrl':               {'addr':0x0020, 'size':1, 'value':0x00, 'mask':0x7F},
              'bias_vco_x3':             {'addr':0x0021, 'size':1, 'value':0x00, 'mask':0x03},
              'bias_pll':                {'addr':0x0022, 'size':1, 'value':0x00, 'mask':0x37},
              'bias_lo':                 {'addr':0x0023, 'size':1, 'value':0x00, 'mask':0x3F},
              'bias_tx':                 {'addr':0x0024, 'size':2, 'value':0x0000, 'mask':0xFFFF},
              'bias_rx':                 {'addr':0x0026, 'size':2, 'value':0x0000, 'mask':0x0FFF},
              #
              'pll_en':                  {'addr':0x0040, 'size':1, 'value':0x00, 'mask':0x7F},
              'pll_divn':                {'addr':0x0041, 'size':1, 'value':0x00, 'mask':0xFF},
              'pll_pfd':                 {'addr':0x0042, 'size':1, 'value':0x00, 'mask':0x07},
              'pll_chp':                 {'addr':0x0043, 'size':1, 'value':0x00, 'mask':0x73},
              'pll_ld_mux_ctrl':         {'addr':0x0044, 'size':1, 'value':0x00, 'mask':0xFF},
              'pll_test_mux_in':         {'addr':0x0045, 'size':1, 'value':0x00, 'mask':0x03},
              'pll_ref_in_lvds_en':      {'addr':0x0046, 'size':1, 'value':0x00, 'mask':0x03},
              #
              'tx_ctrl':                 {'addr':0x0060, 'size':1, 'value':0x10, 'mask':0x7F},
              'tx_bb_q_dco':             {'addr':0x0061, 'size':1, 'value':0x40, 'mask':0x7F},
              'tx_bb_i_dco':             {'addr':0x0062, 'size':1, 'value':0x40, 'mask':0x7F},
              'tx_bb_phase':             {'addr':0x0063, 'size':1, 'value':0x00, 'mask':0x1F},
              'tx_bb_gain':              {'addr':0x0064, 'size':1, 'value':0x00, 'mask':0x23},
              'tx_bb_iq_gain':           {'addr':0x0065, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_bfrf_gain':            {'addr':0x0066, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_bf_pdet_mux':          {'addr':0x0067, 'size':1, 'value':0x00, 'mask':0xBF},
              'tx_alc_ctrl':             {'addr':0x0068, 'size':1, 'value':0x00, 'mask':0xF3},
              'tx_alc_loop_cnt':         {'addr':0x0069, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_alc_start_delay':      {'addr':0x006A, 'size':2, 'value':0x0000, 'mask':0xFFFF},
              'tx_alc_meas_delay':       {'addr':0x006C, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_alc_bfrf_gain_max':    {'addr':0x006D, 'size':1, 'value':0xFF, 'mask':0xFF},
              'tx_alc_bfrf_gain_min':    {'addr':0x006E, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_alc_step_max':         {'addr':0x006F, 'size':1, 'value':0x00, 'mask':0x33},
              'tx_alc_pdet_lo_th':       {'addr':0x0070, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_alc_pdet_hi_offs_th':  {'addr':0x0071, 'size':1, 'value':0x00, 'mask':0x1F},
              'tx_alc_bfrf_gain':        {'addr':0x0072, 'size':1, 'value':0x00, 'mask':0xFF},
              'tx_alc_pdet':             {'addr':0x0073, 'size':1, 'value':0x00, 'mask':0x03},
              #
              'adc_ctrl':                {'addr':0x0080, 'size':1, 'value':0x00, 'mask':0xB7},
              'adc_clk_div':             {'addr':0x0081, 'size':1, 'value':0x03, 'mask':0xFF},
              'adc_sample_cycle':        {'addr':0x0082, 'size':1, 'value':0x00, 'mask':0x3F},
              'adc_num_samples':         {'addr':0x0083, 'size':1, 'value':0x00, 'mask':0x0F}, 
              'adc_sample':              {'addr':0x0090, 'size':2, 'value':0x000, 'mask':0x0FFF},
              'adc_mean':                {'addr':0x0092, 'size':2, 'value':0x000, 'mask':0x0FFF},
              'adc_max':                 {'addr':0x0094, 'size':2, 'value':0x000, 'mask':0x0FFF},
              'adc_min':                 {'addr':0x0096, 'size':2, 'value':0x000, 'mask':0x0FFF},
              'adc_diff':                {'addr':0x0098, 'size':2, 'value':0x0000, 'mask':0x1FFF},
              #
              'vco_en':                  {'addr':0x00A0, 'size':1, 'value':0x00, 'mask':0x7F},
              'vco_dig_tune':            {'addr':0x00A1, 'size':1, 'value':0x00, 'mask':0x7F},
              'vco_ibias':               {'addr':0x00A2, 'size':1, 'value':0x00, 'mask':0x3F},
              'vco_vtune_ctrl':          {'addr':0x00A3, 'size':1, 'value':0x00, 'mask':0x33},
              'vco_vtune_atc_lo_th':     {'addr':0x00A4, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_amux_ctrl':           {'addr':0x00A5, 'size':1, 'value':0x00, 'mask':0x1F},
              'vco_vtune_th':            {'addr':0x00A6, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_atc_hi_th':           {'addr':0x00A7, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_atc_lo_th':           {'addr':0x00A8, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_alc_hi_th':           {'addr':0x00A9, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_override_ctrl':       {'addr':0x00AA, 'size':2, 'value':0x00, 'mask':0x01FF},
              'vco_alc_del':             {'addr':0x00AC, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_vtune_del':           {'addr':0x00AD, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_tune_loop_del':       {'addr':0x00AE, 'size':3, 'value':0x00, 'mask':0x03FFFF},
              'vco_atc_vtune_set_del':   {'addr':0x00B1, 'size':3, 'value':0x00, 'mask':0x03FFFF},
              'vco_atc_vtune_unset_del': {'addr':0x00B4, 'size':3, 'value':0x00, 'mask':0x03FFFF},
              'vco_tune_ctrl':           {'addr':0x00B7, 'size':1, 'value':0x00, 'mask':0x77},
              'vco_tune_status':         {'addr':0x00B8, 'size':1, 'value':0x00, 'mask':0xFF},
              'vco_tune_det_status':     {'addr':0x00B9, 'size':1, 'value':0x00, 'mask':0x0F},
              'vco_tune_freq_cnt':       {'addr':0x00BA, 'size':2, 'value':0x000, 'mask':0x0FFF},
              'vco_tune_dig_tune':       {'addr':0x00BC, 'size':1, 'value':0x40, 'mask':0x7F},
              'vco_tune_ibias':          {'addr':0x00BD, 'size':1, 'value':0x00, 'mask':0x3F},
              'vco_tune_vtune':          {'addr':0x00BE, 'size':1, 'value':0x80, 'mask':0xFF},
              'vco_tune_fd_polarity':    {'addr':0x00BF, 'size':1, 'value':0x01, 'mask':0x01},
              #
              'rx_gain_ctrl_mode':       {'addr':0x00C0, 'size':1, 'value':0x00, 'mask':0x3B},
              'rx_gain_ctrl_reg_index':  {'addr':0x00C1, 'size':1, 'value':0x00, 'mask':0xFF},
              'rx_gain_ctrl_sel':        {'addr':0x00C2, 'size':2, 'value':0x0000, 'mask':0x03FF},
              'rx_gain_ctrl_bfrf':       {'addr':0x00C4, 'size':1, 'value':0x00, 'mask':0xFF},
              'rx_gain_ctrl_bb1':        {'addr':0x00C5, 'size':1, 'value':0x00, 'mask':0xFF},
              'rx_gain_ctrl_bb2':        {'addr':0x00C6, 'size':1, 'value':0x00, 'mask':0xFF},
              'rx_gain_ctrl_bb3':        {'addr':0x00C7, 'size':1, 'value':0x00, 'mask':0xFF},
              'rx_bb_q_dco':             {'addr':0x00C8, 'size':2, 'value':0x40, 'mask':0x3FFF},
              'rx_bb_i_dco':             {'addr':0x00CA, 'size':2, 'value':0x40, 'mask':0x3FFF},
              'rx_dco_en':               {'addr':0x00CC, 'size':1, 'value':0x00, 'mask':0x01},
              'rx_bb_biastrim':          {'addr':0x00CD, 'size':1, 'value':0x00, 'mask':0x3F},
              'rx_bb_test_ctrl':         {'addr':0x00CE, 'size':1, 'value':0x00, 'mask':0xFF},
              #
              'agc_int_ctrl':            {'addr':0x00E0, 'size':1, 'value':0x00, 'mask':0x03},
              'agc_int_en_ctrl':         {'addr':0x00E1, 'size':1, 'value':0x20, 'mask':0x1F},
              'agc_int_backoff':         {'addr':0x00E2, 'size':1, 'value':0x00, 'mask':0xFF},
              'agc_int_start_del':       {'addr':0x00E3, 'size':1, 'value':0x00, 'mask':0xFF},
              'agc_int_timeout':         {'addr':0x00E4, 'size':1, 'value':0x00, 'mask':0xFF},
              'agc_int_gain_change_del': {'addr':0x00E5, 'size':1, 'value':0x05, 'mask':0x0F},
              'agc_int_pdet_en':         {'addr':0x00E6, 'size':1, 'value':0x09, 'mask':0x0F},
              'agc_int_pdet_filt':       {'addr':0x00E7, 'size':2, 'value':0x1F1F, 'mask':0x1FFF},
              'agc_int_pdet_th':         {'addr':0x00E9, 'size':5, 'value':0x0000000000, 'mask':0xFFFFFFFFFF},
              'agc_int_bfrf_gain_lvl':   {'addr':0x00EE, 'size':4, 'value':0xFFCC9966, 'mask':0xFFFFFFFF},
              'agc_int_bb3_gain_lvl':    {'addr':0x00F2, 'size':3, 'value':0xFCA752, 'mask':0xFFFFFF},
              'agc_int_status_pdet':     {'addr':0x00F5, 'size':2, 'value':0xF4, 'mask':0x1FFF},
              'agc_int_status':          {'addr':0x00F7, 'size':1, 'value':0x00, 'mask':0x03},
              'agc_int_gain':            {'addr':0x00F8, 'size':1, 'value':0x00, 'mask':0xFF},
              'agc_int_gain_setting':    {'addr':0x00F9, 'size':4, 'value':0xFFFFFFFF, 'mask':0xFFFFFFFF},
              'agc_ext_ctrl':            {'addr':0x00FD, 'size':1, 'value':0x05, 'mask':0x07},

              #
              'trx_ctrl':                {'addr':0x01C0, 'size':1, 'value':0x00, 'mask':0x3B},
              'trx_soft_ctrl':           {'addr':0x01C1, 'size':1, 'value':0x00, 'mask':0x03},
              'trx_soft_delay':          {'addr':0x01C2, 'size':1, 'value':0x00, 'mask':0x07},
              'trx_soft_max_state':      {'addr':0x01C3, 'size':1, 'value':0x00, 'mask':0x07},
              'trx_tx_on':               {'addr':0x01C4, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF},
              'trx_tx_off':              {'addr':0x01C7, 'size':3, 'value':0x00, 'mask':0x1FFFFF},
              'trx_rx_on':               {'addr':0x01CA, 'size':3, 'value':0x1FFFFF, 'mask':0x1FFFFF},
              'trx_rx_off':              {'addr':0x01CD, 'size':3, 'value':0x00, 'mask':0x1FFFFF},
              'trx_soft_tx_on_enables':  {'addr':0x01E0, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F},
              'trx_soft_rx_on_enables':  {'addr':0x01E8, 'size':8, 'value':0x00, 'mask':0x1F1F1F1F1F1F1F1F},
              'trx_soft_bf_on_grp_sel':  {'addr':0x01F0, 'size':4, 'value':0x00, 'mask':0xFFFFFFFF}
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

