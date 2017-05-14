#!/bin/bash

set -e

git tag -d tmp-test-version-1
git tag -d tmp-test-version-2
git tag -d tmp-test-version-3
git tag -d tmp-test-version-child

git reset --hard tmp-original-master

git branch -D tmp-original-master
