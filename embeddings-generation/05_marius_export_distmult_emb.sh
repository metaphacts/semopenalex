#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=48:00:00 
#SBATCH --mem=376000
#SBATCH --job-name=emb_export_distmult
#SBATCH --output=log_emb_export_distmult.txt
#SBATCH --container-name nv_marius_gpu8_cuda_cudnn_pyxis_container
#SBATCH --container-mounts=/home:/mount_home
#SBATCH --container-writable
#SBATCH --container-remap-root
#SBATCH --gres=gpu:1
echo 'start export'
marius_postprocess --model_dir /mount_home/models/distmult --format parquet --output_dir /mount_home/parquet_export
echo 'Embedding export successful!' 
echo 'start gzip of embeddings'
gzip -k -v --fast /mount_home/parquet_export/embeddings.parquet
echo 'done zipping'
