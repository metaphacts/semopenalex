#!/bin/sh

FOLDER=$(dirname $0)

cd "$FOLDER"

echo "building app in folder $(pwd)"
echo "deleting .DS_Store files"
find . -name .DS_Store -exec rm {} \;

echo "building semopenalex main app"
rm semopenalex-app.zip
zip -r semopenalex-app.zip semopenalex-app

echo "App file:"
find . -name "*-app.zip"
