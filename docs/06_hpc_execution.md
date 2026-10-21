> Curated-results copy: raw reads and regenerable intermediates are excluded; restore final FASTAs with `python3 scripts/restore_artifacts.py`. See [repository guide](14_repository_guide.md) before rerunning stages. Earlier example installer transfers have been superseded by this complete source repository.

# Transfer and PBS execution

The target requires Linux Bash, Python >=3.10 for bootstrap, a site-supported Conda/Mamba manager and PBS/qsub. This repository was not submitted to a real PBS cluster. Consult site policy for queue names, select versus nodes resource syntax, login-node work, transfers and permitted software installation.

## Transfer
Run on your local computer from the parent of this project; replace USER, HOST and DESTINATION with your account, cluster hostname and remote parent directory:
```bash
rsync -av --exclude='.git/' --exclude='.envs/' --exclude='__pycache__/'   --exclude='work/' --exclude='reports/synthetic_demo/'   Oomycete_Contamination/ USER@HOST:DESTINATION/Oomycete_Contamination/
# Alternatively, copy the directory (includes local work unless removed/excluded first):
scp -r Oomycete_Contamination USER@HOST:DESTINATION/
```
Include scripts, hpc, config, environments, metadata, docs, tests, tables and provenance/logs. Downloaded raw FASTQ, checksums and completion manifests can be transferred under data/, along with references and completed analysis outputs. To download directly on HPC instead, exclude data/ and perform stage 01 on an approved transfer/login node. Never transfer locally built environments as working HPC environments. Large Kraken/DIAMOND databases remain external. Preserve archive checksums and resolved version records as provenance.

## Setup on HPC
```bash
cd DESTINATION/Oomycete_Contamination
# First load your site's Conda/Mamba module or initialize its manager.
# Optional: export OOMYCETE_ENV_INIT=/path/to/site/conda_initialization.sh
export OOMYCETE_ENV_DIR="$HOME/.local/share/oomycete-envs"
bash hpc/install_hpc_environment.sh
bash hpc/check_hpc_environment.sh
bash hpc/environment_exec.sh contamination bash tests/test_pipeline.sh
```

Set an existing database in config/config.yaml or export KRAKEN2_DB=/path/to/database for direct local runs. For scheduled jobs, prefer an absolute kraken_db entry in the cluster's config; submit_pipeline.sh explicitly exports a KRAKEN2_DB override if set. Validate hash.k2d, opts.k2d and taxo.k2d with scripts/prepare_database.sh. Record release, taxonomy date and included taxa when known. Bracken additionally needs databaseREADLENGTHmers.kmer_distrib matching read length. Do not assume oomycetes, plants, fungi and RNA viruses are all represented. Set scratch_dir to a site-approved disk directory; no scratch mount or compute-node network is assumed.

## Configure resources and submit
Edit config/hpc_resources.yaml: queue, resource_style (select for PBS Pro/OpenPBS, nodes for Torque), per-stage cpus/memory/walltime, environment_init and environment_dir. The supplied 8 GB screening budget is for a small database; increase it to the actual database requirement. Config threads are overridden by submitted CPU requests. Resource values in YAML are applied by submit_pipeline.sh using qsub flags; PBS does not evaluate shell variables in directives.

```bash
bash hpc/submit_pipeline.sh --phase screening --dry-run
# If downloads already completed, skip the download job:
bash hpc/submit_pipeline.sh --phase screening --skip-download
# If downloads are permitted on compute nodes, permission/configuration is enabled:
bash hpc/submit_pipeline.sh --phase screening
qstat -u "$USER"
```

Screening submits download → QC → subsample/Kraken/Bracken/candidate review, using afterok dependencies. The download runs only when allow_data_download=true. For sites without compute-node internet, run scripts/01_download_data.sh in the contamination environment on an authorized transfer node, then use --skip-download. Similarly retrieve references before mapping on a network-enabled node and leave downloads disabled during compute work. Failed upstream jobs do not release afterok descendants. A qsub submission error stops further submissions and reports already-submitted job IDs.

Review ranked candidate TSVs, copy selected rows into config/candidate_selection.tsv and add verified references. The validation phase refuses to submit without reviewed choices:
```bash
bash hpc/submit_pipeline.sh --phase validation --dry-run
bash hpc/submit_pipeline.sh --phase validation
```

Validation submits reference preparation/mapping → coverage → viral evidence → tables/plots/report. Optional assembly uses the separately recreated viral environment; install --with-viral first and size the job appropriately. For RNA competition, provide a host transcriptome; the default genomic reference lead is not splice-aware.

## Submit an individual wrapper
From the project root this mandatory interface works:
```bash
qsub hpc/pbs/02_qc.pbs
```
It uses conservative literal defaults; your site's default queue must exist. A portable explicit override is:
```bash
qsub -q QUEUE -l select=1:ncpus=4:mem=8gb -l walltime=02:00:00   -v OOMYCETE_PROJECT_ROOT="$PWD",OOMYCETE_THREADS=4   -o "$PWD/logs/pbs" -e "$PWD/logs/pbs" hpc/pbs/02_qc.pbs
```

For Torque, replace select with site-supported nodes=1:ppn=4,mem=8gb and override the wrapper directive on the qsub command line, or use the submission helper with resource_style=nodes. Individual qsub does not read YAML resource requests; pass flags explicitly. If requesting fewer CPUs than the wrapper default, export OOMYCETE_THREADS to the requested count. Submitted paths should contain neither spaces nor commas because PBS -v has site-dependent quoting; the submission helper rejects them clearly. Ordinary local analysis paths may contain spaces.

PBS may spool scripts elsewhere, so wrappers use OOMYCETE_PROJECT_ROOT or walk upward from PBS_O_WORKDIR; they never infer the root from the spool script location. environment_init can load site settings. Normal helper submissions route scheduler spool logs into logs/pbs; individual wrappers stream runtime output there, while the scheduler's initial spool file may still appear in its default location. Every runtime log includes job ID and exit status.

## Monitor, resume and collect
```bash
qstat -u "$USER"
ls -lt logs/pbs/
tail -f logs/pbs/qc_JOBID.log
# Review failure and fix missing input/config/resource issues, then resubmit its wrapper:
qsub hpc/pbs/05_coverage.pbs
```

Replace JOBID with the actual identifier. Verified completed stages skip automatically. Stale outputs fail with an explanation; rebuild locally through the matching stage --force after review, or remove only the relevant completion manifest and rebuild deliberately. Do not blindly delete data or job locks. An interrupted process can leave a .lock file: confirm no matching local/HPC job is running before removing that specific lock. Failed dependency chains often need downstream jobs resubmitted; follow the site's held-job policy rather than assuming automatic release.

Collect outputs from the local machine:
```bash
rsync -av USER@HOST:DESTINATION/Oomycete_Contamination/tables/ Oomycete_Contamination/tables/
rsync -av USER@HOST:DESTINATION/Oomycete_Contamination/figures/ Oomycete_Contamination/figures/
rsync -av USER@HOST:DESTINATION/Oomycete_Contamination/reports/ Oomycete_Contamination/reports/
rsync -av USER@HOST:DESTINATION/Oomycete_Contamination/logs/ Oomycete_Contamination/logs/
```
Retain metadata, config, references metadata/checksums, databases manifest and BAM/coverage results for reproducibility.
