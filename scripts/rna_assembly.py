#!/usr/bin/env python3
"""RNA transcript assembly and BlobToolKit; independent of DNA/FCS results."""
import argparse
import csv
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from common import ROOT, Log, Stage, count_pairs, fasta, path, run, sha, write_json, write_table

def require_files(files):
    """Fail before invoking external software when any required file is absent."""
    for file in files:
        if not Path(file).is_file():raise FileNotFoundError(f"Missing input: {file}")

def command(value):
    """Expand configured command paths while preserving separate executable arguments."""
    return [str(path(x)) if '/' in x and not x.startswith('-') else x for x in value]

def classify_rows(assembly, coverage, assignments, names):
    """Join contig sequence statistics, retained depth and provisional Kraken labels; unknown taxa remain unclassified."""
    rows=[]
    for name, seq in fasta(assembly):
        bases=sum(seq.upper().count(b) for b in 'ACGT')
        taxid=assignments.get(name,'0')
        rows.append(dict(id=name,length=len(seq),gc=sum(seq.upper().count(b) for b in 'GC')/bases if bases else '',mean_depth=coverage.get(name,0),kraken_taxid=taxid,kraken_label=names.get(taxid,'unclassified').replace(' ','_')))
    return rows

def main():
    """Parse this entry point and dispatch independent, restartable analysis stages with input checks."""
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['inspect','assemble','mapping','taxonomy','blobtoolkit'])
    ap.add_argument('--config',default='config/rna_assembly.json')
    ap.add_argument('--force',action='store_true')
    ap.add_argument('--resume',action='store_true',help='Continue interrupted rnaSPAdes using identical inputs and assembly parameters')
    a=ap.parse_args(); c=json.loads(path(a.config).read_text())
    if c.get('schema_version')!=1: raise ValueError('Unsupported configuration')
    os.chdir(ROOT)
    c['threads']=int(os.environ.get('OOMYCETE_THREADS',c['threads']))
    if c['threads']<1:raise ValueError('threads must be positive')
    fa=path(c['assembly']); out=path(c['output']); out.mkdir(parents=True,exist_ok=True)
    with Log('15_rna_'+a.stage,c['sample_id'],'RNA'):
        print('CONFIG',json.dumps(c,sort_keys=True),flush=True)
        if a.stage=='inspect':
            print('Assembly:',fa,'present=',fa.is_file())
            for x in c['reads']:print('Read input:',path(x),'present=',path(x).is_file())
            for exe in ['conda','minimap2','samtools','kraken2']:print('Executable',exe,shutil.which(exe))
            print('External Kraken DB:',c['kraken_db'])
            print('rnaSPAdes memory limit GB:',c['spades_memory_gb'])
            print('Free disk GiB:',shutil.disk_usage(out).free/1024**3)
            print('Unknown strandedness: no --ss flag; coverage is expression-dependent')
            return
        if a.stage=='assemble':
            reads=[path(x) for x in c['reads']];require_files(reads)
            if int(c['spades_memory_gb'])<1:raise ValueError('spades_memory_gb must be positive')
            prefix=command(c['spades_command'])
            # Stable input/options identity permits checkpoint continuation only for the same run.
            pair_count=count_pairs(*reads)
            identity={'input_pairs':pair_count,'reads':{str(x):sha(x) for x in reads},'memory_gb':c['spades_memory_gb'],'threads':c['threads'],'strand_specificity':c['strand_specificity'],'command':prefix}
            if c['strand_specificity'] not in ['unknown','fr','rf']:raise ValueError('strand_specificity must be unknown, fr or rf')
            with Stage(out,'rnaspades',reads,identity,a.force) as st:
                if st.skip:return
                if shutil.disk_usage(out).free < float(c['minimum_free_gb'])*1024**3:raise ValueError('Insufficient configured temporary/output disk reserve')
                work=fa.parent;record=out/'rnaspades_input_identity.json'
                existing=work.exists() and any(work.iterdir())
                if existing:
                    if not a.resume:raise ValueError('Existing rnaSPAdes directory; use --resume for an interrupted identical run, or move it aside for a new run')
                    if not record.exists() or json.loads(record.read_text())!=identity:raise ValueError('Checkpoint inputs/settings differ; resume refused')
                    args=['--continue','-o',str(work)]
                else:
                    if a.resume:raise ValueError('No existing assembly checkpoint to resume')
                    write_json(record,identity)
                    args=['--rna','-1',str(reads[0]),'-2',str(reads[1]),'-t',str(c['threads']),'-m',str(c['spades_memory_gb']),'-o',str(work)]
                    if c['strand_specificity']!='unknown':args+=['--ss',c['strand_specificity']]
                run(prefix+['--version'])
                run(prefix+args)
                require_files([fa,work/'spades.log',work/'params.txt'])
                records=list(fasta(fa))
                if not records:raise ValueError('No assembled transcripts')
                write_json(out/'transcriptome_manifest.json',{'sample_id':c['sample_id'],'transcripts':len(records),'total_bases':sum(len(seq) for _,seq in records),'fasta_sha256':sha(fa),'input_scope':'full cleaned paired RNA reads','strand_specificity':c['strand_specificity'],'identity':identity})
                st.complete([fa,work/'spades.log',work/'params.txt',record,out/'transcriptome_manifest.json'])
            return
        require_files([fa])
        bam=out/'RNA.full_cleaned.filtered.bam'
        # Depth is recomputed from read alignments; assembler header coverage is a different statistic.
        if a.stage=='mapping':
            reads=[path(x) for x in c['reads']];require_files(reads)
            with Stage(out,'rna_mapping',[fa,*reads],c,a.force) as st:
                if st.skip:return
                t=c['threads'];raw=out/'RNA.full_cleaned.bam.partial'
                cmds=[['minimap2','-ax','sr','-t',str(max(1,t-1)),str(fa),*map(str,reads)],['samtools','sort','-@','0','-m','512M','-o',str(raw),'-']]
                print('COMMAND', ' | '.join(shlex.join(x) for x in cmds),flush=True)
                import threading
                def relay(stream):
                    for line in iter(stream.readline,b''):
                        sys.stderr.write(line.decode(errors='replace'));sys.stderr.flush()
                first=subprocess.Popen(cmds[0],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                second=subprocess.Popen(cmds[1],stdin=first.stdout,stderr=subprocess.PIPE);first.stdout.close()
                workers=[threading.Thread(target=relay,args=(proc.stderr,)) for proc in [first,second]]
                for worker in workers:worker.start()
                rc2=second.wait();rc1=first.wait()
                for worker in workers:worker.join()
                if rc1 or rc2:raise RuntimeError(f'Mapping/sorting failed: {rc1}/{rc2}')
                run(['samtools','quickcheck','-v',raw])
                run(['samtools','view','-b','-q',c['min_mapq'],'-F','3844','-o',bam,raw])
                run(['samtools','index',bam]);raw.unlink()
                run(['samtools','coverage',bam],stdout=out/'samtools_coverage.tsv')
                st.complete([bam,Path(str(bam)+'.bai'),out/'samtools_coverage.tsv'])
        # Whole-contig assignments are screening labels; they are not species validation.
        elif a.stage=='taxonomy':
            db=path(c['kraken_db']);idx=[db/(x+'.k2d') for x in ['hash','opts','taxo']];require_files(idx)
            # Index sizes/mtime recorded; no repeated 100 GB checksum of shared DB.
            params=dict(c,index_inventory=[(x.name,x.stat().st_size,x.stat().st_mtime_ns) for x in idx])
            with Stage(out,'rna_taxonomy',[fa],params,a.force) as st:
                if st.skip:return
                run(['kraken2','--db',db,'--threads',c['threads'],'--confidence',c['kraken_confidence'],'--report',out/'assembly.kraken.report.tsv','--output',out/'assembly.kraken.tsv',fa])
                st.complete([out/'assembly.kraken.tsv',out/'assembly.kraken.report.tsv'])
        # Import the same contig IDs into native BlobToolKit, then render browser-free R companions.
        elif a.stage=='blobtoolkit':
            inputs=[out/'samtools_coverage.tsv',out/'assembly.kraken.tsv',out/'assembly.kraken.report.tsv',fa];require_files(inputs)
            with Stage(out,'rna_blobtoolkit',inputs,c,a.force) as st:
                if st.skip:return
                cov={}
                with inputs[0].open() as f:
                    for r in csv.DictReader(f,delimiter='\t'):cov[r['#rname']]=float(r['meandepth'])
                assignments={}
                with inputs[1].open() as f:
                    for line in f:
                        r=line.rstrip().split('\t');assignments[r[1]]=r[2] if r[0]=='C' else '0'
                names={'0':'unclassified'}
                with inputs[2].open() as f:
                    for line in f:
                        r=line.rstrip().split('\t');names[r[4]]=r[5].strip()
                table=out/'contig_evidence.tsv';write_table(table,classify_rows(fa,cov,assignments,names))
                blob=out/'blobdir';partial=out/'blobdir.partial'
                if partial.exists():raise ValueError(f'Inspect/remove incomplete dataset before retry: {partial}')
                prefix=command(c['blobtools_command'])
                run(prefix+['--version'])
                run(prefix+['create','--fasta',str(fa),str(partial)])
                run(prefix+['add','--text',str(table),'--text-header','--text-delimiter','\t','--text-no-array','--text-cols','id=identifiers,mean_depth=assembly_depth,kraken_label=kraken_label',str(partial)])
                run(prefix+['add','--key','plot.y=assembly_depth','--key','plot.cat=kraken_label',str(partial)])
                if blob.exists():
                    if not a.force:raise ValueError('BlobDir exists; use --force after review')
                    saved=out/'blobdir.previous'
                    if saved.exists():raise ValueError('Move blobdir.previous before another forced replacement')
                    blob.rename(saved)
                partial.rename(blob)
                run(['Rscript',ROOT/'scripts/rna_blobplot.R',table,out])
                st.complete([table,*blob.glob('*.json'),out/'rna_blobplot.png',out/'rna_blobplot.pdf'])

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'ERROR {type(error).__name__}: {error}',file=sys.stderr,flush=True);sys.exit(1)
