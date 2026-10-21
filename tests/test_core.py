#!/usr/bin/env python3
import gzip,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from make_fixture import make
class CoreTest(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='oomycete test ');self.d=make(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def cli(self,*args,ok=True):
  p=subprocess.run(['bash',str(ROOT/'scripts/03_subsample.sh'),'--config',str(self.d/'config.yaml'),*args],cwd='/tmp',capture_output=True,text=True)
  self.assertEqual(p.returncode==0,ok,p.stdout+p.stderr);return p
 def test_subsample_restart_and_stale(self):
  self.cli();c=config(self.d/'config.yaml');s=samples(c)[0];out=read_paths(c,s,'subsampled');self.assertEqual(count_pairs(*out),8)
  old=sha(out[0]);self.assertIn('SKIP verified',self.cli().stdout);self.assertEqual(sha(out[0]),old)
  self.cli('--pairs','4',ok=False);self.cli('--pairs','4','--force');self.assertEqual(count_pairs(*out),4)
 def test_pair_errors(self):
  f=self.d/'mismatch.fastq.gz'
  with gzip.open(f,'wt') as g:g.write('@different/2\nA\n+\nI\n')
  with self.assertRaises(ValueError):count_pairs(self.d/'reads_1.fastq.gz',f)
 def test_truncated_fastq(self):
  f=self.d/'broken.fastq';f.write_text('@read\nACGT\n+\n')
  with self.assertRaises(ValueError):list(fastq(f))
 def test_config_validation(self):
  c=json.loads((self.d/'config.yaml').read_text());c['threads']=0;write_json(self.d/'bad.json',c)
  with self.assertRaises(ValueError):config(self.d/'bad.json')
 def test_missing_input(self):
  (self.d/'data/DNA/cleaned/SYNTHETIC_DNA_1.fastq.gz').unlink();p=self.cli(ok=False);self.assertIn('Missing input',p.stderr)
 def test_stage_checksum(self):
  f=self.d/'input';f.write_text('input');o=self.d/'output';o.write_text('output')
  with Stage(self.d,'unit',[f],{'x':1}) as st:st.complete([o])
  with Stage(self.d,'unit',[f],{'x':1}) as st:self.assertTrue(st.skip)
  o.write_text('changed')
  with self.assertRaises(RuntimeError):
   with Stage(self.d,'unit',[f],{'x':1}):pass
 def test_pbs_dryrun(self):
  p=subprocess.run(['bash',str(ROOT/'hpc/submit_pipeline.sh'),'--dry-run','--skip-download','--log-dir',str(self.d/'pbs_logs')],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stderr);self.assertIn('depend=afterok:1.dryrun',p.stdout)
 def test_fake_qsub_dependencies(self):
  fake=self.d/'bin';fake.mkdir();q=fake/'qsub';counter=self.d/'counter'
  q.write_text('#!/usr/bin/env python3\nfrom pathlib import Path\np=Path('+repr(str(counter))+')\nn=int(p.read_text())+1 if p.exists() else 100\np.write_text(str(n))\nprint(str(n)+".mock")\n');q.chmod(0o755)
  p=subprocess.run(['bash',str(ROOT/'hpc/submit_pipeline.sh'),'--skip-download','--log-dir',str(self.d/'pbs_logs')],capture_output=True,text=True,env={**os.environ,'PATH':str(fake)+os.pathsep+os.environ['PATH']})
  self.assertEqual(p.returncode,0,p.stderr);self.assertIn('depend=afterok:100.mock',p.stdout)
 def test_stage_relocation(self):
  # Completion manifests for project-local inputs/outputs survive transfer.
  import common
  old=common.ROOT
  first=self.d/'first';first.mkdir();(first/'scripts').mkdir();(first/'scripts/check.py').write_text('pass')
  inp=first/'input';inp.write_text('input');out=first/'output';out.write_text('output')
  try:
   common.ROOT=first
   with common.Stage(first,'relocate',[inp],{'relative':'input'}) as st:st.complete([out])
   second=self.d/'second';shutil.copytree(first,second);common.ROOT=second
   with common.Stage(second,'relocate',[second/'input'],{'relative':'input'}) as st:self.assertTrue(st.skip)
  finally:common.ROOT=old
 def test_mock_submission_failure_stops_chain(self):
  fake=self.d/'failbin';fake.mkdir();q=fake/'qsub';q.write_text('#!/usr/bin/env bash\necho rejected >&2\nexit 1\n');q.chmod(0o755)
  p=subprocess.run(['bash',str(ROOT/'hpc/submit_pipeline.sh'),'--skip-download','--log-dir',str(self.d/'pbs_logs')],capture_output=True,text=True,env={**os.environ,'PATH':str(fake)+os.pathsep+os.environ['PATH']})
  self.assertNotEqual(p.returncode,0);self.assertIn('qsub rejected',p.stderr);self.assertNotIn('depend=afterok',p.stdout)
 def test_pbs_workdir_root_detection(self):
  root=self.d/'pbs_project';(root/'scripts').mkdir(parents=True);(root/'hpc').mkdir();(root/'scripts/pipeline.py').write_text('# marker')
  (root/'hpc/run_stage.sh').write_text('#!/usr/bin/env bash\nset -eu\n[[ "$PWD" == "$EXPECTED_ROOT" ]]\necho "MOCK_STAGE=$1"\n')
  nested=root/'nested/subdir';nested.mkdir(parents=True)
  env={**os.environ,'PBS_O_WORKDIR':str(nested),'PBS_JOBID':'123.mock','EXPECTED_ROOT':str(root)};env.pop('OOMYCETE_PROJECT_ROOT',None)
  p=subprocess.run(['bash',str(ROOT/'hpc/pbs/02_qc.pbs')],capture_output=True,text=True,env=env,cwd='/tmp')
  self.assertEqual(p.returncode,0,p.stderr);self.assertIn('MOCK_STAGE=qc',p.stdout)
if __name__=='__main__':unittest.main()
