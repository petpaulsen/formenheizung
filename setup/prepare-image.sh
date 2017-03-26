#!/bin/bash

set -e

# download image
wget https://downloads.raspberrypi.org/raspbian_lite_latest -O raspbian.zip
unzip raspbian.zip
mv 2017-03-02-raspbian-jessie-lite.img raspbian.img

# mount image
mkdir image
mount -v -o offset=70254592 -t ext4 raspbian.img image
mount -v -o offset=4194304 -t vfat raspbian.img image/boot

# activate ssh
touch image/boot/shh

# unmount image
umount image/boot
umount image

# show installation message
echo 'copy image with:'
echo '    dd bs=4M if=raspbian.img of=/dev/mmcblk0'
