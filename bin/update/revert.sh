#!/bin/bash

set -e

echo "reverting to version $1... current version is $(git describe)"

git clean -f -d
git reset --hard $1
