#!/bin/bash

export PYTHONPATH=../src

python3 -B -m control ../config.ini &
python3 -B -m webui ../config.ini &
