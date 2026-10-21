import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import rna_assembly

class RNAAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=Path(self.tmp.name)
        root=Path(__file__).resolve().parents[1]
        self.c=json.loads((root/'config/rna_assembly.json').read_text())
        self.c.update(sample_id='RNA_EXTENSION_SYNTHETIC',reads=[str(self.p/'r1.fq'),str(self.p/'r2.fq')],output=str(self.p/'out'),assembly=str(self.p/'out/rnaspades/transcripts.fasta'),minimum_free_gb=0,spades_command=['fake-spades'])
        for read in self.c['reads']:Path(read).write_text('@one\nACGT\n+\nIIII\n')
        self.cfg=self.p/'config.json';self.cfg.write_text(json.dumps(self.c))
        self.calls=[]
    def run_main(self,*args):
        with patch.object(sys,'argv',['rna_assembly.py',*args,'--config',str(self.cfg)]),patch.dict(os.environ,{},clear=False),contextlib.redirect_stdout(io.StringIO()):
            rna_assembly.main()
    def fake_run(self,args,stdout=None):
        args=list(map(str,args));self.calls.append(args)
        if '--version' in args:return
        fa=Path(self.c['assembly']);fa.parent.mkdir(parents=True,exist_ok=True)
        fa.write_text('>transcript_one\nACGTACGT\n')
        (fa.parent/'spades.log').write_text('synthetic mock only\n')
        (fa.parent/'params.txt').write_text('mock arguments\n')
    def test_rna_mode_unknown_strandedness_and_verified_restart(self):
        with patch.object(rna_assembly,'run',side_effect=self.fake_run):
            self.run_main('assemble');self.run_main('assemble')
        self.assertEqual(len(self.calls),2)
        command=self.calls[1]
        self.assertIn('--rna',command)
        self.assertNotIn('--ss',command)
        self.assertIn('-1',command);self.assertIn('-2',command)
        self.assertTrue((self.p/'out/rnaspades.done.json').exists())
        manifest=json.loads((self.p/'out/transcriptome_manifest.json').read_text())
        self.assertEqual(manifest['transcripts'],1)
        self.assertEqual(manifest['total_bases'],8)
    def test_missing_input_stops_before_assembler(self):
        Path(self.c['reads'][0]).unlink()
        with patch.object(rna_assembly,'run') as mocked:
            with self.assertRaises(FileNotFoundError):self.run_main('assemble')
            mocked.assert_not_called()
    def test_checkpoint_resume_and_changed_input_rejection(self):
        def fail(args,stdout=None):
            if '--version' in args:return
            directory=Path(self.c['assembly']).parent;directory.mkdir(parents=True)
            (directory/'params.txt').write_text('mock checkpoint')
            raise RuntimeError('simulated interruption')
        with patch.object(rna_assembly,'run',side_effect=fail):
            with self.assertRaises(RuntimeError):self.run_main('assemble')
        with patch.object(rna_assembly,'run',side_effect=self.fake_run):
            with self.assertRaisesRegex(ValueError,'--resume'):self.run_main('assemble')
            # Input identity prevents accidental continuation with changed reads.
            original=Path(self.c['reads'][0]).read_text()
            Path(self.c['reads'][0]).write_text(original.replace('ACGT','AGGT'))
            with self.assertRaisesRegex(ValueError,'differ'):self.run_main('assemble','--resume')
            Path(self.c['reads'][0]).write_text(original)
            self.run_main('assemble','--resume')
        self.assertIn('--continue',self.calls[-1])
        self.assertNotIn('--rna',self.calls[-1])

class PBSDependencyTests(unittest.TestCase):
    def test_four_jobs_with_correct_dependencies(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'hpc').mkdir();(p/'scripts').mkdir();(p/'bin').mkdir()
            shutil.copy2(root/'hpc/submit_rna_assembly.sh',p/'hpc/submit_rna_assembly.sh')
            (p/'scripts/assembly_analysis.py').touch();(p/'hpc/blobtoolkit_exec.sh').touch()
            fake=p/'bin/qsub'
            fake.write_text('#!/bin/bash\necho "$*" >> "$TEST_LOG"\nn=$(wc -l < "$TEST_LOG")\necho "$n.server"\n');fake.chmod(0o755)
            env=dict(os.environ,PATH=str(p/'bin')+os.pathsep+os.environ['PATH'],TEST_LOG=str(p/'calls'))
            result=subprocess.run(['bash',str(p/'hpc/submit_rna_assembly.sh')],env=env,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            calls=(p/'calls').read_text().splitlines()
            self.assertEqual(len(calls),4)
            self.assertIn('depend=afterok:1.server',calls[1]);self.assertIn('depend=afterok:1.server',calls[2])
            self.assertIn('depend=afterok:2.server:3.server',calls[3])
if __name__=='__main__':unittest.main()
