#!/bin/bash

set -e

git config user.email "test@example.com"
git config user.name "Test"

git branch tmp-original-master
git checkout -B master

touch test-file1
git add test-file1
git commit -m "commit 1"
git tag -m "version 1" tmp-test-version-1

touch test-file2
git add test-file2
git commit -m "commit 2"

touch test-file3
git add test-file3
git commit -m "commit 3"
git tag -m "version 2" tmp-test-version-2

git checkout -b tmp-test-branch
touch test-file4
git add test-file4
git commit -m "commit child"
git tag -m "version cild" tmp-test-version-child

git checkout master
git merge --no-ff -m "Merge branch 'tmp-test-branch'" tmp-test-branch
git tag -m "version 3" tmp-test-version-3

git branch stable

git reset --hard tmp-original-master

git branch -D tmp-test-branch
