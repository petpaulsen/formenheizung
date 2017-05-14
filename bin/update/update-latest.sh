#!/bin/bash

set -e

echo "updating to latest version... current version is $(git describe)"

git fetch -v origin stable:stable
git clean -f -d
git reset --hard $(git describe --abbrev=0 --first-parent stable)
