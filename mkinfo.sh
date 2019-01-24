#!/bin/bash

version=$(cat VERSION)
commit=$(git rev-list -1  $version)
sed -e 's/{TAG}/'"$version"'/g' -e 's/{COMMIT}/'"$commit"'/g' info.template > opacify/opacifyinfo.py 
