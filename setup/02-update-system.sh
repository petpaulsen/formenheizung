#!/bin/bash
# sudo required
# run on Raspberry Pi

set -e

# update packages
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y git

# install python 
sudo apt-get install -y python3-dev libffi-dev libssl-dev
wget https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tgz
tar xzvf Python-3.6.1.tgz
cd Python-3.6.1/
./configure
make
sudo make install
cd ..
rm Python-3.6.1.tgz
sudo rm -rf Python-3.6.1

python3 -m pip install --user numpy scipy matplotlib ipython jupyter pandas sympy nose pyzmq flask RPi.GPIO

# configure startup script
echo '#!/bin/sh -e

/home/pi/run.sh

exit 0' | sudo tee /etc/rc.local

touch /home/pi/run.sh
echo '#!/bin/sh -e

if [ -f /home/pi/data/run.sh ]; then
    bash /home/pi/data/run.sh &
fi' | tee /home/pi/run.sh
chmod a+x /home/pi/run.sh

# prepare mounting of data partition
mkdir /home/pi/data
sudo chmod a+w data
echo 'proc            /proc           proc    defaults             0       0
/dev/mmcblk0p1  /boot           vfat    defaults,ro          0       2
/dev/mmcblk0p2  /               ext4    defaults,noatime,ro  0       1
/dev/mmcblk0p3  /home/pi/data   ext4    defaults,noatime     0       2

tmpfs           /tmp            tmpfs   nosuid,nodev         0       0
tmpfs           /var/log        tmpfs   nosuid,nodev         0       0
tmpfs           /var/tmp        tmpfs   nosuid,nodev         0       0' | sudo tee /etc/fstab

# prepare read-only file system
sudo sed -i 's/$/ fastboot noswap ro/' /boot/cmdline.txt

sudo rm -rf /var/lib/dhcp/ /var/run /var/spool /var/lock /etc/resolv.conf
sudo ln -s /tmp /var/lib/dhcp
sudo ln -s /tmp /var/run
sudo ln -s /tmp /var/spool
sudo ln -s /tmp /var/lock
sudo touch /tmp/dhcpcd.resolv.conf
sudo ln -s /tmp/dhcpcd.resolv.conf /etc/resolv.conf

sudo sed -i "s|PIDFile=/run/dhcpcd.pid|PIDFile=/var/run/dhcpcd.pid|g" /etc/systemd/system/dhcpcd5

# set aliases in bash
echo '
alias ro="sudo mount -o remount,ro / ; sudo mount -o remount,ro /boot"
alias rw="sudo mount -o remount,rw / ; sudo mount -o remount,rw /boot"
' | tee --append ~/.bashrc

# reboot
sudo reboot
