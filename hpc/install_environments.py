#!/usr/bin/env python3
"""Create project-defined Conda environments externally, validating actual executables."""
import argparse,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import *
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config');p.add_argument('--with-viral',action='store_true');p.add_argument('--update',action='store_true',help='Update existing environment when YAML changed');a=p.parse_args()
c=config(a.config);hc=load_yaml(ROOT/'config/hpc_resources.yaml')
prefix=path(os.environ.get('OOMYCETE_ENV_DIR',c['environment_dir'] if a.config else hc.get('environment_dir',c['environment_dir'])))
with Log('install_environments','installation','installations'):
 manager=next((shutil.which(x) for x in ['micromamba','mamba','conda'] if shutil.which(x)),None)
 if not manager and os.environ.get('CONDA_EXE') and Path(os.environ['CONDA_EXE']).is_file():manager=os.environ['CONDA_EXE']
 if not manager:raise SystemExit('No Conda/Mamba detected. Load a cluster Conda module or install a manager separately; no manager was downloaded.')
 prefix.mkdir(parents=True,exist_ok=True)
 records=[]
 for name in ['contamination','plotting']+(['viral_analysis'] if a.with_viral else []):
  yaml=ROOT/'environments'/f'{name}.yml';dest=prefix/name;marker=dest/'.oomycete_yaml.sha256';digest=sha(yaml)
  if (dest/'conda-meta').exists():
   if not marker.exists() or marker.read_text().strip()!=digest:
    if not a.update:raise SystemExit(f'{dest}: YAML changed/untracked; use --update after reviewing')
    cmd=[manager,'env','update','-p',str(dest),'-f',str(yaml)]
   else:cmd=None;print(f'SKIP installed matching YAML: {dest}')
  else:cmd=[manager,'env','create','-p',str(dest),'-f',str(yaml),'-y']
  env={**os.environ,'CONDA_CHANNEL_PRIORITY':'strict','MAMBA_CHANNEL_PRIORITY':'strict'}
  if cmd:
   print('COMMAND '+shlex.join(cmd),flush=True);subprocess.run(cmd,check=True,env=env);marker.write_text(digest+'\n')
  base=[manager,'run']+(['--no-capture-output'] if Path(manager).name=='conda' else [])+['-p',str(dest)]
  tools={'contamination':['prefetch','fasterq-dump','vdb-validate','fastqc','fastp','seqkit','kraken2','bracken','bowtie2','minimap2','samtools','blastn','python','Rscript'],'plotting':['Rscript'],'viral_analysis':['megahit','diamond']}[name]
  for tool in tools:
   flag='version' if tool=='seqkit' else '-version' if tool=='blastn' else ('-v' if tool=='bracken' else '--version')
   cmd=base+['bash','-c','exec '+shlex.join([tool,flag]+(['1'] if tool=='bracken' else []))];print('COMMAND '+shlex.join(cmd),flush=True)
   proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if proc.returncode:raise RuntimeError(f'{name}/{tool} version test failed: {proc.stdout}')
   records.append({'environment':name,'platform':__import__('platform').system()+'-'+__import__('platform').machine(),'tool':tool,'version':' | '.join(proc.stdout.splitlines()[:3]),'status':'executed'})
  explicit=subprocess.run([manager,'list','-p',str(dest),'--explicit'],check=True,stdout=subprocess.PIPE,text=True)
  (ROOT/'environments'/f'{name}.{sys.platform}.explicit.txt').write_text(explicit.stdout)
 write_table(ROOT/'environments/environment_versions.tsv',records)
 (ROOT/'reports/software_installation.md').write_text('# Installation report\n\nCompleted '+now()+'. Environment version checks passed; see environments/environment_versions.tsv and installation log. Platform-specific explicit files are audit artifacts, not portable substitutes for YAML.\n')
