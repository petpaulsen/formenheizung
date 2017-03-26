#!/bin/bash
# sudo required

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
touch image/boot/ssh

# disable automatic resize on boot
sed -i 's| quiet init=/usr/lib/raspi-config/init_resize.sh||' image/boot/cmdline.txt

# unmount image
umount image/boot
umount image

# copy image to sd card
dd bs=4M if=raspbian.img of=/dev/mmcblk0 status=progress

# resize root partition
echo "d
2
n
p
137216
14999999
w
"|fdisk /dev/mmcblk0
e2fsck -f /dev/mmcblk0
resize2fs /dev/mmcblk0

# create additional partition
echo "n
p
3
15000000

w
"|fdisk /dev/mmcblk0
mkfs.ext3 /dev/mmcblk0p3
