#!/bin/bash
# run on Raspberry Pi

set -e

cd ~/data
sudo rm -rf lost+found

# clone repository
git clone https://github.com/petpaulsen/formenheizung.git .
