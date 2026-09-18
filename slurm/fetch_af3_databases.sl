#!/bin/bash
#SBATCH --job-name=af3_db_download
#SBATCH --partition=short
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=af3_db_%j.out
#SBATCH --error=af3_db_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckaycol@bc.edu

set -euo pipefail

AF3_REPO=/projects/bentospr6/mckaycol/alphafold3
DB_DIR=/scratch/mckaycol/alphafold3/databases

mkdir -p "$DB_DIR"

cd "$AF3_REPO"

./fetch_databases.sh "$DB_DIR"
