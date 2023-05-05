#!/bin/bash
#SBATCH --ntasks=1
#SBATCH --time=15:00:00 
#SBATCH --mem=752000
#SBATCH --job-name=marius_train_transe
#SBATCH --output=log_mtrain_transe.txt
#SBATCH --container-name nv_marius_gpu8_cuda_cudnn_pyxis_container
#SBATCH --container-mounts=/home:/mount_home
#SBATCH --container-writable
#SBATCH --container-remap-root
#SBATCH --gres=gpu:1
echo 'Start training with TransE approach'
marius_train /model_configs/transe_100dim_adam_500neg_samples.yaml
echo 'done training epoch'
echo 'start eval'
marius_eval /model_configs/transe_100dim_adam_500neg_samples.yaml
echo 'done eval'
echo 'done with training and evaluation for one epoch'