class Awv():
    """AWV Table class
	Handles access functions to the Antenna Weight Vector Table, controls used index/row
	and associated SRAMs.
    """
    import common
    
    RX = 0
    TX = 1
    
    START_TABLE_TAG = 'START_TABLE FREQ:'
    END_TABLE_TAG   = 'END_TABLE'
    TEMP_TAG        = 'TEMP'
    
    def __init__(self, txrx):
        import memory
        import evk_logger
        self._txrx = txrx
        self.memory = memory.Memory()
        self.logger = evk_logger.EvkLogger()

    def set(self, index):
        if index > 63:
            self.logger.log_info('Error: index should be between 0 and 63')
            return
        ptr = 0x80 | index
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv_ptr', ptr)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv_ptr', ptr)

    def get(self):
        if self._txrx == self.RX:
            return 0x7F & self.memory.awv.rd('bf_rx_awv_ptr')
        elif self._txrx == self.TX:
            return 0x7F & self.memory.awv.rd('bf_tx_awv_ptr')

    def get_table_heads(self, fname):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:    
                self.logger.log_error(fname + ' not found!')
                return
        tags = list()
        line = f.readline()
        while line != '':
            if line.find(self.START_TABLE_TAG) >= 0:
                tags.append(line)
            line = f.readline()
        f.close()
        return tags

    def get_freq_from_head(self, line):
        start = line.find(self.START_TABLE_TAG)+len(self.START_TABLE_TAG)
        end   = line.find(self.TEMP_TAG)
        freq  = float(line[start:end].strip())*1e9
        return freq

    def get_closest_freq_head(self, freq, heads):
        freq_sel = freq
        diff_sel = freq
        head_sel = None
        for head in heads:
            head_freq = self.get_freq_from_head(head)
            diff      = abs(freq - head_freq)
            if diff <= diff_sel:
                freq_sel = head_freq
                diff_sel = diff
                head_sel = head
        return head_sel, freq_sel, diff_sel

        
    def get_table(self, fname, tag):
        try:
            f = open(fname)
        except IOError:
            try:
                f = open('../'+fname)
            except IOError:    
                self.logger.log_error(fname + ' not found!')
                return
        line = ''
        while line[0:len(tag)] != tag:
            line = f.readline()
            if line == '':
                break
        line = f.readline()
        table = ''
        while line[0:len(self.END_TABLE_TAG)] != self.END_TABLE_TAG:
            if line == '':
                break
            table += line
            line = f.readline()
        f.close()
        return table

    def pack_bytes_2_bf_awv(self, q, i):
        pack = lambda q , i : ( ((q & 0x3f) << 6) + (i & 0x3f) )
        return pack(q,i)

    def pack_word_2_bf_awv(self, qi):
        pack = lambda qi : ( ((qi & 0x3f00) >> 2) + (qi & 0x3f) )
        return pack(qi)

    def unpack_bf_awv_2_bytes(self, data):
        return (data >> 6)&0x3f, (data & 0x3f)

    def unpack_bf_awv_2_word(self, data):
        (q,i) = self.unpack_bf_awv_2_bytes(data)
        return (q<<8) + i

    def setup(self, fname, freq, temp=0):
        """Write the beamforming table values for RX or TX.
        The tables are imported from specified CSV file.
        freq is frequency in Hz. temp is temperature in Celcius.
        Example: setup('lut/beambook/bf_rx_awv', 60000000000, 25.0)
        """
        freq = float(freq)
        temp = float(temp)
        if self._txrx != self.RX and self._txrx != self.TX:
            # Wrong parameter value
            self.logger.log_error("First parameter should be RX or TX")
            return
        bf_awv = []
        heads = self.get_table_heads(fname)
        closest_freq_head, closest_freq, diff = self.get_closest_freq_head(freq, heads)
        self.logger.log_info("Using BF Table for frequency {:.2f} GHz".format(closest_freq/1e9),2)
        content = self.get_table(fname, closest_freq_head)
        if content is None:
            self.logger.log_error('Error: File not found.')
            return
        content = content.replace('\r', '').replace('\n', ',').split(',')
        for element in content:
            if element != '' and element != 'X':
                bf_awv.append(int(element,16))

        if len(bf_awv) < 64*32:
            self.logger.log_error('Too small BF table: ' + str(len(bf_awv)),2)
            return
        if len(bf_awv) > 64*32:
            self.logger.log_error('Too large BF table: ' + str(len(bf_awv)),2)
            return


        packed_bf_awv = []
        for index in xrange(0,len(bf_awv)/2):
            packed_bf_awv.append(self.pack_bytes_2_bf_awv(bf_awv[index*2], bf_awv[index*2+1]))
        intbfdata = self.common.intlist2int(packed_bf_awv,0x10000)
        if self._txrx == self.RX:
            self.memory.awv.wr('bf_rx_awv', intbfdata)
        elif self._txrx == self.TX:
            self.memory.awv.wr('bf_tx_awv', intbfdata)

    def _get_element_addr(self, index, ant):
        if index > 63 or ant > 15:
            self.logger.log_error('Error: index or ant out of range')
            return -1
        if self._txrx == self.RX:
            addr = self.memory.awv.addr('bf_rx_awv')
        elif self._txrx == self.TX:
            addr = self.memory.awv.addr('bf_tx_awv')
        addr += (index*32 + (15 - ant)*2)
        return addr


    def rd(self, index, ant):
        """Returns value at location [index,ant] of AWV table.
           Example: Reads value at index 2 antenna 4 of AWV table.
                    rd(2,4)
        """
        value = self.unpack_bf_awv_2_word(self.memory.awv.rd(self._get_element_addr(index, ant), 2))
        return value


    def wr(self, index, ant, value):
        """Writes value to location [index,ant] of AWV table.
           Example: Writes 0x1234 to index 2 antenna 4 of AWV table.
		    Antenna element 4 on row 2 will be set to Q=0x12, I=0x34.
                    wr(2,4,0x1234)
        """
        if isinstance(value,int):
            data = self.pack_word_2_bf_awv(value)
        elif isinstance(value,list) or isinstance(value,tuple):
            data = self.pack_bytes_2_bf_awv(value[0],value[1])
        elif isinstance(value,dict):
            data =  self.pack_bytes_2_bf_awv(value['q'],value['i'])
            
        self.memory.awv.wr(self._get_element_addr(index,ant), data, 2)


    def wr_row(self, index, value, type='w'):
        """Writes the specified value to a index/row in AWV table.
           Example: Write value 0x1234 to index/row 2 in the AWV table.
		    Antenna element 0 on row 2 will be set to Q=0x12, I=0x34, while all other elements
		    on row 2 will be set to Q=0x00, I=0x00.
                    wr_row(2, 0xabab)
        """
        if isinstance(value,int) or isinstance(value,long):
            print map(hex,map(self.pack_word_2_bf_awv,self.common.int2intlist(value,2**16,16)))
            data = self.common.intlist2int(map(self.pack_word_2_bf_awv,self.common.int2intlist(value,2**16,16)),2**16)
        elif isinstance(value,list) or isinstance(value,tuple):
            if len(value) > 16:
                type = 'b'
            if (type == 'b') or (type == 8):
                self.logger.log_error("Row-writes using list/tuple with bytes not supported yet.")
                return
            else:
                data = self.common.intlist2int(map(self.pack_word_2_bf_awv,value),2**16)
        elif isinstance(value,dict):
            self.logger.log_error("Row-writes using dictionary is not supported yet")
            return

        self.memory.awv.wr(self._get_element_addr(index,15), data, 32)


    def dump(self, do_print=True):
        """
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                              AWV_Table (Q=13:8, I=5:0))                                         |")
            self.logger.log_info("     AWV_Ptr |  15     14     13     12     11     10      9      8      7      6       5      4      3      2      1      0   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in xrange(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in xrange(0,16):
                    col_val = self.unpack_bf_awv_2_word((row_val>>((15-col)*16))&0xffff)
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()&0x3f))
        else:
            return values


    def rd_raw(self, index, ant):
        """Returns content of SRAM at location [index,ant] of AWV table.
           Example: Reads SRAM content for index 2 antenna 4 of AWV table.
                    rd_raw(2,4)
        """
        value = self.memory.awv.rd(self._get_element_addr(index, ant), 2)
        return value

    def wr_raw(self, index, ant, value):
        """Writes the specified value to SRAM at location [index,ant] of AWV Table.
           Example: Writes 0x1234 to SRAM for index 2 antenna 4 of AWV table.
                    wr_raw(2,4,0x1234) 
        """
        self.memory.awv.wr(self._get_element_addr(index, ant), value, 2)

    def dump_raw(self, do_print=True):
        """Prints and returns contents of all SRAMs of AWV Table.
        """
        if self._txrx == self.RX:
            values = self.memory.awv.rd('bf_rx_awv')
        elif self._txrx == self.TX:
            values = self.memory.awv.rd('bf_tx_awv')
        else:
            values = None
        if do_print:
            self.logger.log_info("             -------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("             |                                     SRAM for AWV_Table (Q=11:6, I=5:0)                                          |")
            self.logger.log_info("     AWV_Ptr |  15     14     13     12     11     10      9      8      7      6       5      4      3      2      1      0   |")
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            for row in xrange(0,64):
                row_string = '       {:{}}    |'.format(row,2)
                row_val = (values>>((63-row)*16*16))&(2**(16*16)-1)
                for col in xrange(0,16):
                    col_val = (row_val>>((15-col)*16))&0xffff
                    row_string += ' 0x{:0{}X}'.format(int(col_val),4)
                row_string += ' |'
                self.logger.log_info(row_string)
            self.logger.log_info("--------------------------------------------------------------------------------------------------------------------------------")
            self.logger.log_info("Direct AWV_Ptr : " + str(self.get()))
        else:
            return values
