## Graph Entity Embeddings for SemOpenAlex

### Pre-processing, training and export

*01:* Extracts triples from full RDF dump of SemOpenAlex. Mostly, relevant entity <> entity relations are extracted. Also auxiliary classes are cut short, i.e. intermediate hops are eliminated.

*02:* Map all URIs to integers: enumerate entities and relation identifiers separately, write this conversion to a dict for later re-substitution.

*03:* Import the edge list in integer form with Marius to ready for training, produces .bin format files. In addition, the modified source code file of the employed Marius system is given to reproduce the altered Marius import sequence in the directory *marius_code_modifications*. For Marius, see [Marius GitHub](https://github.com/marius-team/marius).

*04:* Embeddings training using five different approaches. Carry out evaluation after each epoch. Re-run the bash script for each epoch subsequently. The included `.sh` shell scripts trigger one epoch of embedding training using the `.yaml` model configuration files in the directory *model_configs*.

*05:* Export the embedding vectors for subsequent use using `marius_postprocess`.


### Technical details

All processes regarding Marius were executed in a container environment for HPC settings using the Enroot framework for Docker containers. 
The container image is `nvidia+cuda+11.2.2-cudnn8-devel-ubuntu18.04.sqsh` from [NVidia](https://catalog.ngc.nvidia.com/containers).
In our setup we used a system running RHEL 8.4, using Python 3.7, Marius 0.0.2, PyTorch 1.9.1 and CUDA 11.2.2. for embeddings generation. 
