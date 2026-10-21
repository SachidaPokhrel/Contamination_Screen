import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from assembly_analysis import classify_rows

class AssemblyEvidenceTests(unittest.TestCase):
    def test_multicontig_zero_coverage_gc_and_taxonomy(self):
        with tempfile.TemporaryDirectory() as tmp:
            fa=Path(tmp)/'a.fa'
            fa.write_text('>one description\nACGTNN\n>two\nNNNN\n>three\nGGCC\n')
            rows=classify_rows(fa,{'one':2.5},{'one':'4779'},{'4779':'Bremia lactucae'})
            self.assertEqual(rows[0]['gc'],0.5)
            self.assertEqual(rows[0]['length'],6)
            self.assertEqual(rows[0]['mean_depth'],2.5)
            self.assertEqual(rows[0]['kraken_label'],'Bremia_lactucae')
            self.assertEqual(rows[1]['gc'],'')
            self.assertEqual(rows[1]['mean_depth'],0)
            self.assertEqual(rows[1]['kraken_label'],'unclassified')
            self.assertEqual(rows[2]['gc'],1)

class SubmissionTests(unittest.TestCase):
    def test_pbs_afterok_and_optional_fcs(self):
        import os
        import shutil
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'hpc').mkdir()
            (root/'references/host').mkdir(parents=True)
            (root/'references/host/Gokan_CBS315_81.fa').write_text('>a\nACGT\n')
            source=Path(__file__).resolve().parents[1]/'hpc/submit_assembly_analysis.sh'
            shutil.copy2(source,root/'hpc/submit_assembly_analysis.sh')
            fake=root/'bin';fake.mkdir()
            q=fake/'qsub'
            q.write_text('#!/bin/bash\necho "$*" >> "$TEST_QSUB_LOG"\necho "123.server"\n')
            q.chmod(0o755)
            env=dict(os.environ,PATH=str(fake)+os.pathsep+os.environ['PATH'],TEST_QSUB_LOG=str(root/'calls'))
            proc=subprocess.run(['bash',str(root/'hpc/submit_assembly_analysis.sh'),'--with-fcs'],env=env,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            lines=(root/'calls').read_text().splitlines()
            self.assertEqual(len(lines),4)
            self.assertIn('depend=afterok:123.server:123.server',lines[2])
            self.assertIn('assembly_fcs.pbs',lines[3])

class EntryPointTests(unittest.TestCase):
    def test_help_and_missing_assembly(self):
        import json
        import subprocess
        root=Path(__file__).resolve().parents[1]
        proc=subprocess.run([sys.executable,str(root/'scripts/assembly_analysis.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)
        with tempfile.TemporaryDirectory() as tmp:
            config=json.loads((root/'config/assembly_analysis.json').read_text())
            config.update(assembly=str(Path(tmp)/'missing.fa'),output=str(Path(tmp)/'out'))
            cfg=Path(tmp)/'config.json';cfg.write_text(json.dumps(config))
            proc=subprocess.run([sys.executable,str(root/'scripts/assembly_analysis.py'),'mapping','--config',str(cfg)],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('Missing input:',proc.stderr)

if __name__=='__main__':unittest.main()
