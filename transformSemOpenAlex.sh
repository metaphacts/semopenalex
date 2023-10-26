#!/bin/bash

# this script collects and run the following python scripts in sequentially

echo "SemOpenAlex transformation script started at: " $(date -u)

# Data transformation from OpenAlex to RDF data dump
# Running a series of python scripts one after another
python3 ./transformation-scripts/semopenalex-concepts.py;
python3 ./transformation-scripts/semopenalex-funders.py; 
python3 ./transformation-scripts/semopenalex-institutions.py; 
python3 ./transformation-scripts/semopenalex-publishers.py; 
python3 ./transformation-scripts/semopenalex-sources.py; 
python3 ./transformation-scripts/semopenalex-authors.py;
python3 ./transformation-scripts/semopenalex-works.py;
python3 ./transformation-scripts/semopenalex-dataset.py;

# make sure to clean graphdb storage folder before ingesting data
rm -rf ./graphdb-preload/graphdb-home/data/repositories/metaphactory/storage

# load RDF data dump .gzip files to graphdb using preload tool
docker-compose -f ./graphdb-preload/docker-compose.yml up;

# gzip graphdb-home/ folder to transfrom to a dedicated server
echo "Started to tar.gz graphdb-home/ folder at: " $(date -u)
tar -czvf graphdb-home.tar.gz ./graphdb-preload/graphdb-home/ 
echo "SemOpenAlex transformation script ended at: " $(date -u)
