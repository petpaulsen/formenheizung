#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR=$DIR/..

export PYTHONPATH=$ROOT_DIR/app

cd $ROOT_DIR

python3 -B -m update config.ini &
python3 -B -m control config.ini --log /tmp/controller.log &
python3 -B -m webui config.ini --log /tmp/webui.log &
