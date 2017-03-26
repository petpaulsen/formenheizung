#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR/../src

python3 -B -m control $DIR/../config.ini --log /tmp/controller.log &
python3 -B -m webui $DIR/../config.ini --log /tmp/webui.log &
