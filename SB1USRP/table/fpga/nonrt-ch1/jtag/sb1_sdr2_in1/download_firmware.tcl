connect

puts stderr "INFO: Configuring the FPGA..."
puts stderr "INFO: Downloading bitstream: system.bit to the target."

targets -set -nocase -filter {name =~ "*PS TAP*"}
fpga "../common/system.bit"

targets -set -nocase -filter {name =~ "*PSU*"}
mask_write 0xFFCA0038 0x1C0 0x1C0
targets -set -nocase -filter {name =~ "*MicroBlaze PMU*"}
catch {stop}; after 1000

puts stderr "INFO: Downloading ELF file: pmufw.elf to the target."
dow  "../common/pmufw.elf"

after 2000
con
targets -set -nocase -filter {name =~ "*APU*"}
mwr 0xffff0000 0x14000000
mask_write 0xFD1A0104 0x501 0x0
targets -set -nocase -filter {name =~ "*A53*#0"}

source ../common/psu_init.tcl

puts stderr "INFO: Downloading ELF file: zynqmp_fsbl.elf to the target."
dow  "../common/zynqmp_fsbl.elf"

after 2000
con

after 4000; stop; catch {stop}; psu_ps_pl_isolation_removal; psu_ps_pl_reset_config
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Downloading ELF file: u-boot.elf to the target."
dow  "../common/u-boot.elf"

after 2000
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Loading image: Image at 0x00200000"
dow -data  "../common/Image" 0x00200000

after 2000
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Loading image: system.dtb at 0x00100000"
dow -data  "../common/system.dtb" 0x00100000

after 2000
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Loading image: rootfs.cpio.gz.u-boot at 0x04000000"
dow -data  "rootfs.cpio.gz.u-boot" 0x04000000

after 2000
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Loading image: boot.scr at 0x20000000"
dow -data  "../common/boot.scr" 0x20000000

after 2000
targets -set -nocase -filter {name =~ "*A53*#0"}
puts stderr "INFO: Downloading ELF file: bl31.elf to the target."
dow  "../common/bl31.elf"

after 2000
con
exit
