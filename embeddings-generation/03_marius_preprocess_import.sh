#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=4:00:00 
#SBATCH --mem=376000
#SBATCH --job-name=marius_preprocess_all
#SBATCH --output=log_marius_preprocess_all.txt
#SBATCH --container-name nv_marius_cuda_cudnn_pyxis_container
#SBATCH --container-mounts=/home:/mount_home
#SBATCH --container-writable
#SBATCH --container-remap-root
echo 'Start Marius import of data to ready graph for embeddings training'
marius_preprocess --output_dir /mount_home/marius_imported/ --edges /mount_home/raw_data/extracted_triples.csv -d ',' --dataset_split 0.998 0.001 0.001 --columns 0 1 2 --num_partitions 1 --no_remap_ids --overwrite
echo 'Marius import worked - all preprocessed'