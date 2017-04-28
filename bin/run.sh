#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

export PYTHONPATH=$DIR/../src

cd $DIR/..

python3 -B src/run.py --controller-log /tmp/controller.log --webui-log /tmp/webui.log &
