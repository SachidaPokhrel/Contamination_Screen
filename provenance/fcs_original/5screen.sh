#!/bin/bash

module purge

GXDB_LOC="/datasets/unzipped/fcs/gxdb"
FCSPY="/apps/x86-64/apps/fcs_0.5.0/fcs.py"
FASTA="GCA_051997085.1.fasta"

export FCS_DEFAULT_IMAGE="/apps/x86-64/apps/fcs_0.5.0/fcs-gx.sif"

python3 "$FCSPY" screen genome \
    --fasta "$FASTA" \
    --out-dir ./decontamination/ \
    --gx-db "$GXDB_LOC" \
    --tax-id 36331
