#!/usr/bin/env python3
"""Generate clearly labeled synthetic reads, exact SAM/depth fixtures, and isolated config."""
import argparse,gzip,json,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import ROOT,config,write_table,write_json

def make(dest):
 dest=Path(dest).resolve();dest.mkdir(parents=True,exist_ok=True);rng=random.Random(731)
 seq=''.join(rng.choice('ACGT') for _ in range(1200));zero=''.join(rng.choice('ACGT') for _ in range(800));host=''.join(rng.choice('ACGT') for _ in range(1000))
 (dest/'candidate.fa').write_text('>covered\n'+seq+'\n>zero\n'+zero+'\n');(dest/'host.fa').write_text('>host\n'+host+'\n')
 rc=lambda s:s.translate(str.maketrans('ACGT','TGCA'))[::-1]
 for mate in (1,2):
  with gzip.open(dest/f'reads_{mate}.fastq.gz','wt') as f:
   for i in range(12):
    start=0 if i<6 else 400
    read=(seq[start:start+100] if mate==1 else rc(seq[start+200:start+300])) if i<10 else ''.join(rng.choice('ACGT') for _ in range(100))
    f.write(f'@pair{i}/{mate}\n{read}\n+\n'+('I'*100)+'\n')
 contigs=[{'contig':'fixture__covered','reference_id':'fixture','original_contig':'covered','length':1200,'role':'candidate','taxid':'2','organism':'SYNTHETIC fixture organism'}, {'contig':'fixture__zero','reference_id':'fixture','original_contig':'zero','length':800,'role':'candidate','taxid':'2','organism':'SYNTHETIC fixture organism'}]
 write_table(dest/'contigs.tsv',contigs)
 with open(dest/'known.sam','w') as f:
  f.write('@HD\tVN:1.6\tSO:coordinate\n@SQ\tSN:fixture__covered\tLN:1200\n@SQ\tSN:fixture__zero\tLN:800\n')
  records=[]
  for i in range(10):
   start=0 if i<6 else 400
   for flag,pos,read in [(99,start+1,seq[start:start+100]),(147,start+201,seq[start+200:start+300])]:
    records.append((pos,f'pair{i}\t{flag}\tfixture__covered\t{pos}\t42\t100M\t=\t{start+201 if flag==99 else start+1}\t{300 if flag==99 else -300}\t{read}\t'+('I'*100)+'\n'))
  f.writelines(r for _,r in sorted(records))
 with open(dest/'known_depth.tsv','w') as f:
  for chrom,L in [('fixture__covered',1200),('fixture__zero',800)]:
   for pos in range(1,L+1):
    dep=(6 if pos<=100 or 201<=pos<=300 else 4 if 401<=pos<=500 or 601<=pos<=700 else 0) if chrom=='fixture__covered' else 0
    f.write(f'{chrom}\t{pos}\t{dep}\n')
 ds=[{'sample_id':'SYNTHETIC_DNA','assay':'DNA','sra_run':'','organism':'SYNTHETIC','expected_taxids':'3','raw_r1':str(dest/'reads_1.fastq.gz'),'raw_r2':str(dest/'reads_2.fastq.gz'),'sra_bytes':'0','enabled':'true'}]
 write_table(dest/'datasets.tsv',ds)
 write_table(dest/'references.tsv',[{'reference_id':'fixture','role':'candidate','taxid':'2','organism':'SYNTHETIC fixture organism','accessions':'','fasta':str(dest/'candidate.fa'),'evidence_url':'synthetic fixture; not NCBI','verified':'true'},{'reference_id':'hostfixture','role':'host','taxid':'3','organism':'SYNTHETIC host','accessions':'','fasta':str(dest/'host.fa'),'evidence_url':'synthetic fixture; not NCBI','verified':'true'}])
 write_table(dest/'selection.tsv',[{'sample_id':'SYNTHETIC_DNA','taxid':'2','reference_id':'fixture','selected':'true','note':'known synthetic spike-in'}])
 c=config();c.pop('_config_file',None);c.update(allow_data_download=False,datasets=str(dest/'datasets.tsv'),references=str(dest/'references.tsv'),selection=str(dest/'selection.tsv'),data_dir=str(dest/'data'),results_dir=str(dest/'results'),scratch_dir=str(dest/'scratch'),readset='raw',subsample_pairs=8,competitive_mapping=True,expected_taxids=['3'],expected_names=['SYNTHETIC host'])
 for i in (1,2):
  target=dest/'data/DNA/cleaned'/f'SYNTHETIC_DNA_{i}.fastq.gz';target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((dest/f'reads_{i}.fastq.gz').read_bytes())
 write_json(dest/'config.yaml',c)
 write_json(dest/'expected.json',{'supporting_reads':20,'supporting_fragments':10,'input_reads':24,'input_fragments':12,'reference_length':2000,'mean_depth':1.0,'breadth_1x_percent':20.0,'breadth_5x_percent':10.0,'breadth_10x_percent':0.0,'read_fraction_percent':100*20/24})
 (dest/'README.md').write_text('# Synthetic fixture only\n\nknown.sam and known_depth.tsv were constructed with exact expected coordinates; these are not outputs of Bowtie2 or SAMtools. Real-tool tests write separate results and are skipped if tools are missing.\n')
 return dest
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('destination');a=p.parse_args();print(make(a.destination))
