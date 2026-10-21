#!/usr/bin/env python3
import tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import table
from pipeline import summarize_depth,alignment_counts
from make_fixture import make
class CoverageTest(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.d=make(self.tmp.name);self.ct=table(self.d/'contigs.tsv')
 def tearDown(self):self.tmp.cleanup()
 def test_known_multicontig(self):
  m=summarize_depth(self.d/'known_depth.tsv',self.ct)['fixture']
  for k,v in {'reference_length':2000,'covered_bases':400,'mean_depth':1,'breadth_1x_percent':20,'breadth_5x_percent':10,'breadth_10x_percent':0}.items():self.assertAlmostEqual(m[k],v)
 def test_sparse_and_zero_contig(self):
  f=self.d/'sparse.tsv';f.write_text('fixture__covered\t1\t10\n');m=summarize_depth(f,self.ct)['fixture'];self.assertEqual(m['mean_depth'],10/2000);self.assertEqual(m['breadth_10x_percent'],.05)
 def test_all_zero(self):
  f=self.d/'empty.tsv';f.write_text('');m=summarize_depth(f,self.ct)['fixture'];self.assertEqual(m['mean_depth'],0);self.assertEqual(m['breadth_1x_percent'],0)
 def test_reads_vs_fragments(self):
  m=alignment_counts(self.d/'known.sam',self.ct,self.d/'test.sqlite')['fixture'];self.assertEqual(m['supporting_reads'],20);self.assertEqual(m['supporting_fragments'],10);self.assertEqual(m['mean_mapq'],42);self.assertEqual(m['median_mapq'],42)
  self.assertAlmostEqual(100*m['supporting_reads']/24,83.33333333333333)
 def test_invalid_duplicate_position(self):
  f=self.d/'bad.tsv';f.write_text('fixture__covered\t1\t1\nfixture__covered\t1\t2\n')
  with self.assertRaises(ValueError):summarize_depth(f,self.ct)
if __name__=='__main__':unittest.main()
