#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=30:00:00 
#SBATCH --mem=752000
#SBATCH --job-name=marius_train_gnn
#SBATCH --output=log_mtrain_gnn.txt
#SBATCH --container-name nv_marius_gpu8_cuda_cudnn_pyxis_container
#SBATCH --container-mounts=/home:/mount_home
#SBATCH --container-writable
#SBATCH --container-remap-root
#SBATCH --gres=gpu:1
echo 'Start training with GNN setup'
marius_train /model_configs/gnn_100dim_adam_500neg_samples.yaml
echo 'done training epoch'
echo 'start eval'
marius_eval /model_configs/gnn_100dim_adam_500neg_samples.yaml
echo 'done eval'
echo 'done with training and evaluation for one epoch'