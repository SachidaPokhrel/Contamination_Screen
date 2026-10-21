#!/usr/bin/env python3
"""Test download orchestration with fake SRA executables; no archive/network validation claim."""
import gzip,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import ROOT,write_table,write_json,count_pairs,sha
from make_fixture import make
class DownloadControlTest(unittest.TestCase):
 def test_mock_prefetch_validation_conversion_restart_permission(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)/'project';shutil.copytree(ROOT/'scripts',root/'scripts');(root/'config').mkdir();(root/'metadata').mkdir()
   fixture=make(Path(tmp)/'input');c=json.loads((fixture/'config.yaml').read_text());rows=[{'sample_id':'SYNTHETIC_DNA','assay':'DNA','sra_run':'SRR000001','organism':'synthetic','expected_taxids':'','raw_r1':'','raw_r2':'','sra_bytes':'1','enabled':'true'}]
   write_table(root/'config/datasets.tsv',rows);write_table(root/'metadata/download_manifest.tsv',[],['sample_id','assay','run','path','sha256','bytes','verified_at'])
   c.update(datasets='config/datasets.tsv',data_dir='data',scratch_dir='work',allow_data_download=False,minimum_free_gb=0)
   write_json(root/'config/config.yaml',c);bin=Path(tmp)/'bin';bin.mkdir();trace=Path(tmp)/'trace'
   # A single command dispatcher creates only synthetic fixture artifacts.
   script='''#!/usr/bin/env python3
import gzip,os,sys
from pathlib import Path
name=Path(sys.argv[0]).name
if '--version' in sys.argv: print(name+' MOCK_VERSION');raise SystemExit(0)
with open(os.environ['TRACE'],'a') as log:log.write(name+'\\n')
args=sys.argv[1:]
if name=='prefetch':
 out=Path(args[args.index('-O')+1]);run=args[-1];d=out/run;d.mkdir(parents=True,exist_ok=True);(d/(run+'.sra')).write_text('SYNTHETIC ARCHIVE; NOT SRA')
elif name=='vdb-validate':
 assert Path(args[0]).read_text().startswith('SYNTHETIC')
elif name=='fasterq-dump':
 out=Path(args[args.index('--outdir')+1]);out.mkdir(exist_ok=True);run=Path(args[0]).name
 for i in (1,2):
  with gzip.open(Path(os.environ['FIXTURE'])/f'reads_{i}.fastq.gz','rb') as src:(out/f'{run}_{i}.fastq').write_bytes(src.read())
'''
   for tool in ['prefetch','vdb-validate','fasterq-dump']:
    f=bin/tool;f.write_text(script);f.chmod(0o755)
   env={**os.environ,'PATH':str(bin)+os.pathsep+os.environ['PATH'],'FIXTURE':str(fixture),'TRACE':str(trace)}
   cmd=['bash',str(root/'scripts/01_download_data.sh')]
   def call():return subprocess.run(cmd,env=env,cwd='/tmp',capture_output=True,text=True)
   p=call();self.assertNotEqual(p.returncode,0);self.assertIn('Download disabled',p.stderr);self.assertFalse(trace.exists())
   c['allow_data_download']=True;write_json(root/'config/config.yaml',c);p=call();self.assertEqual(p.returncode,0,p.stdout+p.stderr)
   self.assertEqual(trace.read_text().splitlines(),['prefetch','vdb-validate','fasterq-dump'])
   out=root/'data/DNA/raw';self.assertEqual(count_pairs(out/'SYNTHETIC_DNA_1.fastq.gz',out/'SYNTHETIC_DNA_2.fastq.gz'),12)
   before=trace.read_text();p=call();self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertIn('SKIP verified',p.stdout);self.assertEqual(trace.read_text(),before)
if __name__=='__main__':unittest.main()
