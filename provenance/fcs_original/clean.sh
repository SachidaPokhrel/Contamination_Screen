# Set the FCS-GX Singularity container image
export FCS_DEFAULT_IMAGE="/apps/x86-64/apps/fcs_0.5.0/fcs-gx.sif"

# Confirm that the image exists
ls -lh "$FCS_DEFAULT_IMAGE"

# Check Singularity availability
which singularity

# Clean the genome
cat GCA_051997085.1.fasta | python3 /apps/x86-64/apps/fcs_0.5.0/fcs.py clean genome \
    --action-report ./decontamination/GCA_051997085.1.36331.fcs_gx_report.txt \
    --output clean.fasta \
    --contam-fasta-out contaminated.fasta
