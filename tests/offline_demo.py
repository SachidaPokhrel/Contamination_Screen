#!/usr/bin/env python3
"""Run a small local demo; SAM/depth/classifier inputs are explicit fixtures, never real-tool results."""
import argparse,csv,gzip,json,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT,write_table,write_json,table
from pipeline import summarize_depth,alignment_counts
from make_fixture import make

def demo(dest):
 dest=Path(dest).resolve();dest.mkdir(parents=True,exist_ok=True)
 shutil.copytree(ROOT/'scripts',dest/'scripts',dirs_exist_ok=True)
 for d in ['config','tables','reports','logs','figures']: (dest/d).mkdir(exist_ok=True)
 w=make(dest/'test_input');c=json.loads((w/'config.yaml').read_text())
 # All demo configuration paths are relative to the relocated demo project.
 for k in ['datasets','references','selection','data_dir','results_dir','scratch_dir']:
  c[k]=str(Path(c[k]).relative_to(dest))
 for file,keys in [('datasets.tsv',['raw_r1','raw_r2']),('references.tsv',['fasta'])]:
  rows=table(w/file)
  for r in rows:
   for k in keys:r[k]=str(Path(r[k]).relative_to(dest))
  write_table(w/file,rows)
 c['environment_dir']='.envs';write_json(dest/'config/config.yaml',c)
 def call(*args):
  print('DEMO COMMAND',*args,flush=True);subprocess.run(args,check=True,cwd=dest)
 call('bash',str(dest/'scripts/run_pipeline.sh'),'--from-stage','subsample','--to-stage','subsample','--force')
 kr=dest/'test_input/results/DNA/02_kraken2/SYNTHETIC_DNA';kr.mkdir(parents=True,exist_ok=True)
 (kr/'kraken.report.tsv').write_text('100.00\t12\t0\tR\t1\troot\n83.33\t10\t10\tS\t2\t  SYNTHETIC fixture organism\n16.67\t2\t2\tS\t3\t  SYNTHETIC host\n')
 write_json(kr/'screen.json',{'release':'SYNTHETIC fixture (no Kraken2 executed)','taxonomy_date':'not applicable'})
 call(sys.executable,str(dest/'scripts/06_select_candidates.py'),'--force')
 contigs=table(w/'contigs.tsv');coverage=summarize_depth(w/'known_depth.tsv',contigs)['fixture'];counts=alignment_counts(w/'known.sam',contigs,w/'counts.sqlite')['fixture']
 row={'sample_id':'SYNTHETIC_DNA','assay':'DNA','reference_id':'fixture','taxid':'2','organism':'SYNTHETIC fixture organism','role':'candidate','mapping_mode':'candidate_only','readset':'raw',**coverage,**counts,'input_reads':24,'input_fragments':12,'read_fraction_percent':100*counts['supporting_reads']/24,'fragment_fraction_percent':100*counts['supporting_fragments']/12,'min_mapq':20,'min_baseq':0,'excluded_flags':3844,'mapq_255_excluded':True,'mate_overlap_removed_for_depth':True,'fragment_policy':'either_mate_per_reference','duplicate_policy':'exclude_flagged','rna_reference_warning':'','evidence_origin':'constructed known-coordinate SAM/depth fixtures; no external mapper executed'}
 for mode in ['candidate_only','competitive']:
  row['mapping_mode']=mode;out=dest/'test_input/results/DNA/06_coverage/SYNTHETIC_DNA'/mode/'coverage.tsv';write_table(out,[row])
 call('bash',str(dest/'scripts/run_pipeline.sh'),'--from-stage','table','--to-stage','table')
 call(sys.executable,str(dest/'scripts/13_generate_report.py'),'--force')
 (dest/'README.md').write_text('# Executed offline synthetic demo\n\nSubsampling, candidate-table parsing, known-coordinate coverage aggregation, detection-table joins and report generation ran locally. Kraken, alignment and per-position depth inputs were constructed fixtures. No SRA download, FastQC, fastp, Kraken2, Bowtie2, SAMtools or R executable ran in this demo. This directory must not be interpreted as biological evidence.\n')
 print('OFFLINE DEMO OUTPUT',dest)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',default=str(ROOT/'reports/synthetic_demo'));a=p.parse_args();demo(a.output)
