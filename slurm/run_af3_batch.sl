#!/bin/bash
#SBATCH --job-name=af3_batch
#SBATCH --partition=short
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=af3_batch_%j.out
#SBATCH --error=af3_batch_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckaycol@bc.edu

cd /projects/bentospr6/mckaycol

singularity exec --userns --nv \
  --bind /scratch/mckaycol/alphafold3:/scratch/mckaycol/alphafold3 \
  --bind /projects/bentospr6/mckaycol/aptamer-case-study:/projects/bentospr6/mckaycol/aptamer-case-study \
  alphafold3_sandbox \
  python /app/alphafold/run_alphafold.py \
  --input_dir=/projects/bentospr6/mckaycol/aptamer-case-study/af3_inputs \
  --model_dir=/scratch/mckaycol/alphafold3/models \
  --db_dir=/scratch/mckaycol/alphafold3/databases \
  --output_dir=/projects/bentospr6/mckaycol/aptamer-case-study/af3_outputs/batch_1
