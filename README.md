# SemOpenAlex
[SemOpenAlex](https://semopenalex.org) is a scientific publications dataset, presently in the form of a knowledge graph. 
It also offered as the basis for Knowledge Graph augmentation together with some possible use-cases that can enable AI-driven decision making. 

The underlying [SemOpenAlex](https://semopenalex.org) dataset was based on [OpenAlex](https://docs.openalex.org) where the snapshot of [OpenAlex](https://docs.openalex.org/download-snapshot) was updated about once per month, so did the SemOpenAlex.

Here the following sections below, we describe the detailed steps to perform before executing one main script. 

## SemOpenAlex Dataset
To generate SemOpenAlex dataset from [OpenAlex](https://openalex.s3.amazonaws.com/browse.html) s3 bucket,
we use the following python scripts for each entity. 

1. [semopenalex-concepts.py](./transformation-scripts/semopenalex-concepts.py)
2. [semopenalex-institutions.py](./transformation-scripts/semopenalex-institutions.py)
3. [semopenalex-venues.py](./transformation-scripts/semopenalex-venues.py)
4. [semopenalex-authors.py](./transformation-scripts/semopenalex-authors.py)
5. [semopenalex-works.py](./transformation-scripts/semopenalex-works.py)

Note, [semopenalex-dataset.py](./transformation-scripts/semopenalex-dataset.py) script is used to capture metadata about SemOpenAlex dataset.

### Prerequisites 
To be able to run above python scripts, we need:
- python 3.7 (or later version)
- python's package management tool pip

Linux Server/OS: 
- disk storage space of at least 7TB (to store temp openalex data dump)
- vCPU with at least 8 threads
- RAM at least 128GB

GraphDB:
- 10.0.0 (or later version)
- docker installed (version >= 17.x , check with docker --version)
- docker-compose installed (version >= 1.14, check with docker-compose --version)

### Python libraries installation 
The required python libraries are defined at `requirements.txt` file and you need to run the following command to install all dependencies.

```
$ pip install -r requirements.txt
```

### Adjust location for OpenAlex data dump root directory
In order to execute one main script, 
it needs `data_dump_input_root_dir` location to define and you can modify and adjust the following directory inside all the python scripts code:

For example, ideal location `/opt/openalex-snapshot`. Note, ideal location must be mounted to a disk storage with at least 5TB. 
```
data_dump_input_root_dir = '/opt/openalex-snapshot'
```

### Tuning python scripts for multiprocessing
Depending on resource available to your Linux server, you can adjust multiprocessing for the following python scripts:

1. [semopenalex-authors.py](./transformation-scripts/semopenalex-authors.py)
2. [semopenalex-works.py](./transformation-scripts/semopenalex-works.py) 

Currently, `CPU_THREADS` is default to 16 and `maxtasksperchild` id default to 5.


### Tuning GraphDB  
In order to load SemOpenAlex RDF dataset, billions of statements to GraphDB, 
we use [ImportRDF](https://graphdb.ontotext.com/documentation/10.0/loading-data-using-importrdf.html) tool, 
specifically [preload](https://graphdb.ontotext.com/documentation/10.0/loading-data-using-importrdf.html#preload-command-line-options) with docker.
To achieve an optimal performance for loading such large amounts of RDF data, we recommend using GraphDB SE/EE license features (for example, multi-threading).

Note, GraphDB can be started without a license pre-configured. As of GraphDB 10 the database will operate in Free Mode. 
To activate GraphDB SE/EE features, a valid license can be set at the following place:

```
./graphdb-preload/graphdb-license/graphdb.license
```

You may also need to tune memory reservations, memory limits for the Docker and 
min and max values for Java heap memory for GraphDB according to the available resources: [docker-compose.yml](./graphdb-preload/docker-compose.yml)


### Executing one main script

Before executing the following one main bash script to run all python scripts and data ingestion to GraphDB, there are few things you need to consider.

First, to perform data transformation step: from OpenAlex to SemOpenAlex RDF dataset, 
it typically takes up to 1-2 days or at least in our config for OS (vCPU: 16 and RAM 256 GB).

Second, to perform data ingestion to GraphDB, it also typically takes up 1-2 days. 
The overall time taken may depend and may be faster if you have bigger the computation power.

Third, we compress `graphdb-home/` folder. 
This is for us to transfer folder to another dedicated server. 
You can skip or disable this step if you intended to run GraphDB in the same server.

Another note, in order to avoid the main script to be accidentally terminated, 
we recommend using linux `screen` or alike command to run it in the background. 

```
$ chmod +x transformSemOpenAlex.sh
$ ./transformSemOpenAlex.sh
```