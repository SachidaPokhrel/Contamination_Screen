#!/usr/bin/env python3
"""Retrieve small NCBI RunInfo metadata; never downloads sequence data or enables downloads."""
import argparse,csv,io,json,sys,time,urllib.parse
from pathlib import Path
from common import *
from pipeline import fetch
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config');p.add_argument('--query',help='Optional NCBI SRA metadata search expression, e.g. SAMN13878576[BioSample]');p.add_argument('--retmax',type=int,default=20);a=p.parse_args()
with Log('verify_dataset_metadata'):
 c=config(a.config);d=ROOT/'metadata/ncbi';d.mkdir(parents=True,exist_ok=True)
 if a.query:
  if not 1<=a.retmax<=100:raise ValueError('Metadata discovery capped at 100 experiments')
  q=d/'discovery_search.json';fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'+urllib.parse.urlencode({'db':'sra','term':a.query,'retmode':'json','retmax':a.retmax}),q,5_000_000)
  ids=json.loads(q.read_text())['esearchresult']['idlist']
  if not ids:raise SystemExit('No matching SRA experiment metadata')
  time.sleep(.4);f=d/'discovery_runinfo.csv';fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'sra','id':','.join(ids),'rettype':'runinfo','retmode':'text'}),f,20_000_000)
  print(f'Inspect {f}; select exactly one run rather than automatically enabling all discovered runs')
 else:
  status=[]
  for s in samples(c):
   run=s['sra_run'];ident(run);f=d/(run+'.runinfo.csv')
   fetch('https://trace.ncbi.nlm.nih.gov/Traces/sra-db-be/run_new?'+urllib.parse.urlencode({'acc':run}),f,5_000_000)
   # Some NCBI endpoints return HTML; fall back to EUtils RunInfo.
   rows=list(csv.DictReader(io.StringIO(f.read_text())))
   if not rows or 'Run' not in rows[0]:
    fetch('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'sra','id':run,'rettype':'runinfo','retmode':'text'}),f,5_000_000)
    rows=list(csv.DictReader(io.StringIO(f.read_text())))
   rows=[r for r in rows if r.get('Run')==run]
   if len(rows)!=1:raise ValueError(f'{run}: exact run metadata not returned; no metadata has been invented')
   r=rows[0]
   if r.get('LibraryLayout')!='PAIRED':raise ValueError(f'{run} is not reported paired')
   if r.get('LibraryStrategy')!=('WGS' if s['assay']=='DNA' else 'RNA-Seq'):raise ValueError(f'{run}: strategy disagrees with assay')
   status.append({'sample_id':s['sample_id'],'run':run,'bioproject':r.get('BioProject',''),'biosample':r.get('BioSample',''),'spots':r.get('spots',''),'bases':r.get('bases',''),'avgLength':r.get('avgLength',''),'size_MB':r.get('size_MB',''),'metadata_sha256':sha(f),'verified_at':now()})
   time.sleep(.4)
  write_table(d/'verification.tsv',status);print('Metadata saved; review read-length conventions, download sizes and permission before editing config.')
