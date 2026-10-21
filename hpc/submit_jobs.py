#!/usr/bin/env python3
"""Submit afterok PBS chains; screening and manual candidate validation are separate phases."""
import argparse,os,re,shlex,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import *
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=['screening','validation'],default='screening');p.add_argument('--skip-download',action='store_true');p.add_argument('--dry-run',action='store_true');p.add_argument('--resources',default='config/hpc_resources.yaml');p.add_argument('--config',default='config/config.yaml');p.add_argument('--log-dir',default='logs/pbs');a=p.parse_args()
r=load_yaml(path(a.resources));c=config(a.config)
plan=[('download','01_download.pbs'),('qc','02_qc.pbs'),('screen','03_screen.pbs')] if a.phase=='screening' else [('mapping','04_mapping.pbs'),('coverage','05_coverage.pbs'),('viral_analysis','06_viral_analysis.pbs'),('reports','07_reports.pbs')]
if a.skip_download:plan=[x for x in plan if x[0]!='download']
if a.phase=='validation':
 from pipeline import references_rows,selected
 refs=references_rows(c)
 for s in samples(c):selected(c,s,refs)
logdir=path(a.log_dir);logdir.mkdir(parents=True,exist_ok=True)
# PBS -v is a comma-delimited format; reject values that cannot be represented portably.
values={'OOMYCETE_PROJECT_ROOT':str(ROOT),'OOMYCETE_CONFIG':str(path(a.config))}
for name in ['OOMYCETE_ENV_DIR','OOMYCETE_ENV_INIT','KRAKEN2_DB']:
 if os.environ.get(name):values[name]=os.environ[name]
if any(re.search(r'[,\s]',v) for v in values.values()):raise SystemExit('PBS exported paths must not contain commas/whitespace; use a cluster directory without these characters')
last=None;jobs=[]
with Log('submit_pipeline','submission','pbs'):
 for stage,file in plan:
  z=r['stages'][stage];cpus=int(z['cpus']);mem=z['memory'];wall=z['walltime']
  if cpus<1 or not re.fullmatch(r'\d+(?:gb|mb)',mem,re.I) or not re.fullmatch(r'\d+:\d{2}:\d{2}',wall):raise ValueError('Invalid resource configuration')
  resource=f'select=1:ncpus={cpus}:mem={mem}' if r.get('resource_style','select')=='select' else f'nodes=1:ppn={cpus},mem={mem}'
  export={**values,'OOMYCETE_THREADS':str(cpus)}
  cmd=['qsub','-N','oom_'+stage,'-l',resource,'-l','walltime='+wall,'-v',','.join(k+'='+v for k,v in export.items()),'-o',str(logdir),'-e',str(logdir)]
  # Stage-specific queues avoid sending a 96 GB screen to the site's 4 GB default queue.
  queue=z.get('queue') or r.get('queue')
  if queue:cmd+=['-q',queue]
  if last:cmd+=['-W','depend=afterok:'+last]
  cmd+=[str(ROOT/'hpc/pbs'/file)]
  print('COMMAND '+shlex.join(cmd),flush=True)
  if a.dry_run:job=f'{len(jobs)+1}.dryrun'
  else:
   proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   if proc.returncode:raise RuntimeError(f'qsub rejected {stage}: {proc.stderr}; already submitted jobs: {jobs}')
   job=proc.stdout.strip()
   if not re.fullmatch(r'[0-9]+(?:\[\])?(?:\.[A-Za-z0-9_.-]+)?',job):raise RuntimeError(f'Unexpected qsub job ID: {job!r}; inspect scheduler before retrying')
  jobs.append({'stage':stage,'job_id':job,'submitted_at':now(),'dry_run':a.dry_run});last=job
 write_table(logdir/('submission_'+a.phase+('_dryrun' if a.dry_run else '')+'.tsv'),jobs)
 print('Job chain:',jobs)
