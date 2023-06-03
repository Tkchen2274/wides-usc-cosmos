# Eder python environment can be started in 2 ways:
python -i eder.py [Device descriptor]  for example: python -i eder.py RX
# or
python
import eder
eder=eder.Eder(unit_name=[Device descriptor])  for example: eder=eder.Eder(unit_name='TX')  
# If Evald0 is powered and connected, both methods of startup produce the same
# initial response:
# "Chip present! (chip_id = 0x02711702)"


# After the above startup, the following commands are avaliable:
# General
# =======
eder.reset()				- HW reset of Eder
eder.check()	     	      	  	- Checks that Eder is present
eder.tx_setup(freq)		  	- Prepares Eder for TX mode
eder.tx_enable()			- Enables TX mode
eder.tx_disable()			- Disables TX mode
eder.rx_setup(freq)		  	- Prepares Eder for RX mode
eder.rx_enable()			- Enables RX mode
eder.rx_disable()			- Disables RX mode
eder.fpga_clk(True|False)   	    	- Turn on/off dig_clk to FPGA

# Registers
# =========
eder.regs.dump()			- Dump contents of all non-memory related
				          registers.
eder.regs.wr('<reg_name>',<val>)  	- Write register <reg_name> with <val>.
eder.regs.rd('<reg_name>')  	  	- Read register <reg_name>.
eder.regs.wrrd('<reg_name>',<val>)	- Write register <reg_name> with <val> and
				          the read register.
eder.regs.set('<reg_name>',<val>) 	- Set specified <val>-bits in register
				    	  <reg_name> (<val> OR register).
eder.regs.clr('<reg_name>',<val>) 	- Clear specified <val>-bits in register
				    	  <reg_name> (NOT <val> AND register).
eder.regs.tgl('<reg_name>',<val>) 	- Toggle specified <val>-bits in register
				    	  <reg_name> (<val> XOR register).



# Memory
# =========
eder.mems.dump()			- Dump contents of all memory related
				    	  registers.
eder.mems.wr('<reg_name>',<val>)  	- Write memory-register <reg_name> with <val>.
eder.mems.rd('<reg_name>')  	  	- Read memory-register <reg_name>.
eder.mems.wrrd('<reg_name>',<val>)	- Write memory-register <reg_name> with <val>
				    	  and then read memory-register.
eder.mems.set('<reg_name>',<val>)   	- Set specified <val>-bits in memory-register
				    	  <reg_name> (<val> OR memory-register).
eder.mems.clr('<reg_name>',<val>) 	- Clear specified <val>-bits in
				    	  memory-register <reg_name>
				    	  (NOT <val> AND memory-register).
eder.mems.tgl('<reg_name>',<val>) 	- Toggle specified <val>-bits in
				    	  memory-register <reg_name>
				    	  (<val> XOR register).



# Ref
# ===
eder.ref.init()				- Initialise 45 MHz reference
eder.ref.monitor()   		  	- Output reference/2 on LD



# Vco
# ===
eder.vco.init()				- Initialise VCO
eder.vco.set([dig_tune,[ibias]])  	- Set override values for VCO.
eder.vco.monitor([divn])	  	- Output vco/(2*divn) on LD.



# Pll
# ===
eder.pll.init()				- Initialise PLL.
				    	  This calls ref.init() and vco.init()
eder.pll.set(frequency)		  	- Set PLL frequency and run VCO-tune
eder.pll.monitor()		  	- Output vco/(2*divn) on LD.



# Adc
# ===
eder.adc.init(div,cycle,set_edge)	- Initialise ADC.
eder.adc.start(src)		  	- Start the ADC collecting samples from AMUX src
eder.adc.stop()			  	- Stop the ADC
eder.adc.edge(set_edge)		  	- Set sampling edge
eder.adc.dump(nos)		  	- Generate a list with nos number of samples
eder.adc.mean(value_list)	  	- Calculate mean of list of values
eder.adc.max(value_list)	  	- Find max among list of values
eder.adc.min(value_list)	  	- Find min among list of values



BF General description
======================
# BF consists of two main function-blocks, BF AWV and BF IDX, and a pointer (active AWV_Ptr) controlling
# which AWV is currently being applied to the antennas.
# BF AWV consists of a table (AWV Table) with 64 AWV:s to apply to the antennas and a pointer (direct AWV_Ptr)
# selecting which AWV to use from the table.
# BF IDX consists of a table (IDX Table) with AWV_Ptr:s and an index (IDX_index) selecting which AWV_Ptr
# (indirect AWV_Ptr) to use from the IDX Table.
#
# At each time the active AWV_Ptr is either (X=tx or rx):
#   1. The direct AWV_Ptr. It becomes the active AWV_Ptr whenever eder.X.bf.awv.set(row) is used.
#   2. The indirect AWV_Ptr. It becomes the active AWV_Ptr whenever anyone of eder.X.bf.idx.rst(),
#      eder.X.bf.idx.rtn() and eder.X.bf.idx.inc() is used.


# TX
# ==
eder.tx.setup(freq)			- Setup TX using BF-table based on freq.
eder.tx.enable()		    	- Enable TX mode
eder.tx.disable()		    	- Disable TX mode


# TX BF
# =====
eder.tx.bf.dump([True|False])     	- Dump contents of TX BF IDX Table along with contents from
				          TX BF AWV Table. The contents of each row printed is:
					  index IDX_Table[index] AWV_Table[IDX_Table[index]]
				          True (default): prints the table
					  False: Returns the contents of the tables as a dictionary
					  	 with two keys; awv and idx, and values equal to integer
						 representations of table contents.

# TX BF AWV
# =========
eder.tx.bf.awv.setup(fname,freq,temp)	- Setup TX BF AWV Table from file <fname> based on freq and temp.
eder.tx.bf.awv.dump([True|False])     	- Dump contents of TX BF AWV table.
				          True (default): prints the table
					  False: Returns the contents of the table as an integer
eder.tx.bf.awv.wr(row,col,data)       	- Write <data> to position row,col in TX BF AWV Table
eder.tx.bf.awv.rd(row,col)            	- Read data from position row,col in TX BF AWV Table
eder.tx.bf.awv.set(row)		      	- Sets the direct AWV_Ptr and applies it as the active AWV_Ptr.
eder.tx.bf.awv.get()		      	- Gets what the direct AWV_Ptr is set to.

# TX BF IDX
# =========
eder.tx.bf.idx.setup(fname,freq,temp)	- Setup TX BF IDX Table from file <fname> based on freq.
eder.tx.bf.idx.dump([True|False])     	- Dump contents of TX BF IDX table
				          True (default): prints the table
					  False: Returns the contents of the table as an integer
eder.tx.bf.idx.wr(index,data)           - Write <data> to index <index> in TX BF IDX Table
eder.tx.bf.idx.rd(index)                - Read data from index <index> in TX BF IDX Table
eder.tx.bf.idx.set(index)		- Sets the RST/RTN index
eder.tx.bf.idx.get()		      	- Gets the RST/RTN index
eder.tx.bf.idx.rst()			- Sets IDX_index equal to RST/RTN index, sets indirect AWV_Ptr equal to
					  the AWV_Ptr selected by RST/RTN index and makes the active
					  AWV_Ptr equal to indirect AWV_Ptr.
eder.tx.bf.idx.rtn()			- Sets the indirect AWV_Ptr to the AWV_Ptr selected by
					  RST/RTN index from IDX Table and makes it the active AWV_Ptr.
					  The IDX_index is NOT changed.
eder.tx.bf.idx.inc()			- Increments IDX_index, sets indirect AWV_Ptr equal to the
					  AWV_Ptr selected by the incremented IDX_index and makes the active AWV_Ptr
					  equal to the indirect AWV_Ptr.


# TX DCO
# ======
eder.tx.dco.init()			- Initialises TX DCO compensation
eder.tx.dco.sweep()			- Runs TX DCO without setting compensation
eder.tx.dco.run()			- Runs TX DCO compensation




# RX
# ==
eder.rx.setup(freq)			- Setup RX using BF-table based on freq.
eder.rx.enable()		    	- Enable RX mode
eder.rx.disable()		    	- Disable RX mode


# RX BF
# =====
eder.rx.bf.dump([True|False])     	- Dump contents of RX BF IDX Table along with contents from
				          RX BF AWV Table. The contents of each row printed is:
					  index IDX_Table[index] AWV_Table[IDX_Table[index]]
				          True (default): prints the table
					  False: Returns the contents of the tables as a dictionary
					  	 with two keys; awv and idx, and values equal to integer
						 representations of table contents.

# RX BF AWV
# =========
eder.rx.bf.awv.setup(fname,freq,temp)	- Setup RX BF AWV Table from file <fname> based on freq and temp.
eder.rx.bf.awv.dump([True|False])     	- Dump contents of RX BF AWV table.
				          True (default): prints the table
					  False: Returns the contents of the table as an integer
eder.rx.bf.awv.wr(row,col,data)       	- Write <data> to position row,col in RX BF AWV Table
eder.rx.bf.awv.rd(row,col)            	- Read data from position row,col in RX BF AWV Table
eder.rx.bf.awv.set(row)		      	- Sets the direct AWV_Ptr and applies it as the active AWV_Ptr.
eder.rx.bf.awv.get()		      	- Gets what the direct AWV_Ptr is set to.

# RX BF IDX
# =========
eder.rx.bf.idx.setup(fname,freq,temp)	- Setup RX BF IDX Table from file <fname> based on freq.
eder.rx.bf.idx.dump([True|False])     	- Dump contents of RX BF IDX table
				          True (default): prints the table
					  False: Returns the contents of the table as an integer
eder.rx.bf.idx.wr(index,data)           - Write <data> to index <index> in RX BF IDX Table
eder.rx.bf.idx.rd(index)                - Read data from index <index> in RX BF IDX Table
eder.rx.bf.idx.set(index)		- Sets the RST/RTN index
eder.rx.bf.idx.get()		      	- Gets the RST/RTN index
eder.rx.bf.idx.rst()			- Sets IDX_index equal to RST/RTN index, sets indirect AWV_Ptr equal to
					  the AWV_Ptr selected by RST/RTN index and makes the active
					  AWV_Ptr equal to indirect AWV_Ptr.
eder.rx.bf.idx.rtn()			- Sets the indirect AWV_Ptr to the AWV_Ptr selected by
					  RST/RTN index from IDX Table and makes it the active AWV_Ptr.
					  The IDX_index is NOT changed.
eder.rx.bf.idx.inc()			- Increments IDX_index, sets indirect AWV_Ptr equal to the
					  AWV_Ptr selected by the incremented IDX_index and makes the active AWV_Ptr
					  equal to the indirect AWV_Ptr.

# RX DCO
# ======
eder.rx.dco.init()			- Initialises RX DCO compensation
eder.rx.dco.report()			- Reports differential and common mode Voltages at RX BB output
eder.rx.dco.sweep()			- Runs RX DCO without setting compensation
eder.rx.dco.run()			- Runs RX DCO compensation
