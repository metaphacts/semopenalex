# SemOpenAlex
[SemOpenAlex](https://semopenalex.org) is a dataset about scientific publications presented in the form of a knowledge graph. 

The underlying [SemOpenAlex](https://semopenalex.org) dataset is based on [OpenAlex](https://docs.openalex.org). The original dataset snapshots of [OpenAlex](https://docs.openalex.org/download-snapshot) are updated about once per month. With the scripts provided in this repository, the SemOpenAlex
dataset can be re-generated based on the snapshot.

In the sections below, we describe the detailed steps create and load the SemOpenAlex dataset.

## SemOpenAlex Dataset

To generate the SemOpenAlex dataset from the [OpenAlex](https://openalex.s3.amazonaws.com/browse.html) S3 bucket,
we use the following python scripts for each entity. Each individual script downloads the latest snapshot and
produces a RDF document in the TRIG format.

1. [semopenalex-authors.py](./transformation-scripts/semopenalex-authors.py)
2. [semopenalex-concepts.py](./transformation-scripts/semopenalex-concepts.py)
2. [semopenalex-institutions.py](./transformation-scripts/semopenalex-institutions.py)
3. [semopenalex-publishers.py](./transformation-scripts/semopenalex-publishers.py)
3. [semopenalex-sources.py](./transformation-scripts/semopenalex-sources.py)
5. [semopenalex-works.py](./transformation-scripts/semopenalex-works.py)
6. [semopenalex-funders.py](./transformation-scripts/semopenalex-funders.py)

Note that the [semopenalex-dataset.py](./transformation-scripts/semopenalex-dataset.py) script is used to capture metadata about SemOpenAlex dataset (e.g. when it was loaded).

### Prerequisites 

To be able to run the above Python scripts, we need:
- Python 3.7 (or later)
- Python's package management tool `pip`

Linux Server/OS: 
- disk storage space of at least 4TB
- vCPU 16
- RAM of at least 256GB

GraphDB:
- 10.0.0 (or later)
- Docker installed (version >= 17.x , check with docker --version)
- docker-compose installed (version >= 1.14, check with docker-compose --version)

### Python libraries installation 

The required Python libraries are defined in the `requirements.txt` file. The following command can be used to install all dependencies.

```
$ pip install -r requirements.txt
```

### Adjust the location for the OpenAlex data dump root directory
In order to execute the main script, 
it requires the `data_dump_input_root_dir` location to be defined. You can modify and adjust the following directory inside all the Python scripts code as needed.

The default location is `/opt/openalex-snapshot`. Note that the folder must be mounted to a disk storage with at least 5TB. 

```
data_dump_input_root_dir = '/opt/openalex-snapshot'
```

### Tuning Python scripts for multiprocessing
Depending on resources available on your Linux server, you can fine-tune multiprocessing for the following Python scripts:

1. [semopenalex-authors.py](./transformation-scripts/semopenalex-authors.py)
2. [semopenalex-works.py](./transformation-scripts/semopenalex-works.py) 

Currently, `CPU_THREADS` defaults to 16 and `maxtasksperchild` id defaults to 5.


### Tuning GraphDB  
In order to load the SemOpenAlex RDF dataset (i.e. billions of statements) to GraphDB, 
we use the [ImportRDF](https://graphdb.ontotext.com/documentation/10.0/loading-data-using-importrdf.html) tool, 
specifically [preload](https://graphdb.ontotext.com/documentation/10.0/loading-data-using-importrdf.html#preload-command-line-options) with docker.
To achieve an optimal performance for loading such large amounts of RDF data, we recommend using GraphDB SE/EE features (for example, multi-threading).

Note, that GraphDB can be started without a license pre-configured. As of GraphDB 10 the database will operate in Free Mode. 
To activate GraphDB SE/EE features, a valid license can be copied to the following place:

```
./graphdb-preload/graphdb-license/graphdb.license
```

You may also need to tune memory reservations, memory limits for the Docker and 
min and max values for Java heap memory for GraphDB according to the available resources, see [docker-compose.yml](./graphdb-preload/docker-compose.yml)


### Executing the main script

Before executing the following single main script (which runs all Python scripts as well as the data ingestion to GraphDB), there are few things you need to consider.

First, to perform data transformation step: from OpenAlex to SemOpenAlex RDF dataset, 
it typically takes at least 3-4 days in our system environment (vCPU: 16 and RAM 256 GB).

Second, to perform data ingestion to GraphDB, it also typically takes up 2-3 days. 
The overall time taken may depend and may be faster if you have bigger the computation power.

Third, we compress `graphdb-home/` folder. 
This is for us to transfer the folder to another dedicated server for hosting the production database. 
You can skip or disable this step if you intend to run GraphDB in the same server.

Another note, in order to avoid the main script to be accidentally terminated, 
we recommend using linux `screen` or alike command to run it in the background. 

```
$ chmod +x transformSemOpenAlex.sh
$ ./transformSemOpenAlex.sh
```
