#!/bin/bash

COMMIT=$(git describe --abbrev=0 --first-parent stable 2> /dev/null)
while [ $? -eq 0 ]; do
    echo $COMMIT
    COMMIT=$(git describe --abbrev=0 --first-parent $COMMIT^1 2> /dev/null)
done
exit 0
