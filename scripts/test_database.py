#!/usr/bin/env python3
"""Build a tiny synthetic Kraken2 database from local generated references; no network."""
import argparse,random
from pathlib import Path
from common import *
p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination');a=p.parse_args()
with Log('build_test_database'):
 d=path(a.destination)
 if d.exists() and any(d.iterdir()):raise ValueError('Use an empty destination directory')
 tax=d/'taxonomy';tax.mkdir(parents=True,exist_ok=True)
 (tax/'nodes.dmp').write_text('1\t|\t1\t|\tno rank\t|\t\t|\t0\t|\t0\t|\t1\t|\t0\t|\t0\t|\t0\t|\t0\t|\t0\t|\t\t|\n2\t|\t1\t|\tspecies\t|\t\t|\t0\t|\t0\t|\t1\t|\t0\t|\t0\t|\t0\t|\t0\t|\t0\t|\t\t|\n3\t|\t1\t|\tspecies\t|\t\t|\t0\t|\t0\t|\t1\t|\t0\t|\t0\t|\t0\t|\t0\t|\t0\t|\t\t|\n')
 (tax/'names.dmp').write_text('1\t|\troot\t|\t\t|\tscientific name\t|\n2\t|\tSYNTHETIC candidate\t|\t\t|\tscientific name\t|\n3\t|\tSYNTHETIC host\t|\t\t|\tscientific name\t|\n')
 rng=random.Random(731);fa=d/'synthetic.fa';fa.write_text(''.join(f'>kraken:taxid|{i}|synthetic_{i}\n'+''.join(rng.choice('ACGT') for _ in range(2000))+'\n' for i in (2,3)))
 run(['kraken2-build','--add-to-library',fa,'--db',d]);run(['kraken2-build','--build','--threads',2,'--db',d])
 require=[d/n for n in ['hash.k2d','opts.k2d','taxo.k2d']]
 if not all(x.is_file() and x.stat().st_size for x in require):raise RuntimeError('Kraken2 build did not produce valid index files')
 write_json(d/'TEST_ONLY.json',{'warning':'Entirely synthetic custom taxonomy; taxids 2/3 are artificial labels and not NCBI meanings','seed':731,'time':now(),'checksums':{x.name:sha(x) for x in require}})
 print(f'Test database: {d}; never use for biological screening')
