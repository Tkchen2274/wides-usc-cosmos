#!/bin/bash

PLNX="../apu/plnx/images/linux"

cp $PLNX/system.bit ./common/
cp $PLNX/pmufw.elf ./common/
cp $PLNX/../../project-spec/hw-description/psu_init.tcl ./common/
cp $PLNX/zynqmp_fsbl.elf ./common/
cp $PLNX/u-boot.elf ./common/
cp $PLNX/Image ./common/
cp $PLNX/system.dtb ./common/
cp $PLNX/boot.scr ./common/
cp $PLNX/bl31.elf ./common

while read -p "Enter rootfs dir: " -r
do
  if [[ -d $REPLY ]]; then
    cp $PLNX/rootfs.cpio.gz.u-boot $REPLY
    break
  else
    echo "Error: "$REPLY" doesn't exist"
  fi
done
