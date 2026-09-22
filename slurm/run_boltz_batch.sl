#!/bin/bash
#SBATCH --job-name=boltz_batch
#SBATCH --partition=short
#SBATCH --gres=gpu:l40s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=boltz_batch_%j.out
#SBATCH --error=boltz_batch_%j.err
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=mckaycol@bc.edu

set -euo pipefail

PROJECT=/projects/bentospr6/mckaycol/aptamer-case-study
BOLTZ_REPO=/projects/bentospr6/mckaycol/boltz
BOLTZ_BIN=/projects/bentospr6/mckaycol/boltz/.conda-env/bin/boltz

INPUT_DIR="$PROJECT/boltz_inputs"
OUTPUT_DIR="$PROJECT/boltz_outputs/batch_1"

mkdir -p "$OUTPUT_DIR"

echo "========================================"
echo "Boltz-2 aptamer affinity batch"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "Inputs: $(find "$INPUT_DIR" -maxdepth 1 -name '*.yaml' | wc -l)"
echo "========================================"

nvidia-smi

cd "$BOLTZ_REPO"

"$BOLTZ_BIN" predict "$INPUT_DIR" \
    --out_dir "$OUTPUT_DIR" \
    --model boltz2 \
    --use_msa_server \
    --no_kernels

echo "========================================"
echo "Finished: $(date)"
echo "========================================"
