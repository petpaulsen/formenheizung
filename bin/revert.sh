#!/bin/bash

set -e

git clean -f -d
git reset --hard $1
