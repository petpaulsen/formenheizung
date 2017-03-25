#!/bin/bash
python3 -m control config.ini &
python3 webui/ui.py &
