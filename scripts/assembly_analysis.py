#!/usr/bin/env python3
"""Optional DNA assembly analysis; does not alter read-based results."""
import argparse
import csv
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from common import ROOT, Log, Stage, fasta, path, run, sha, write_json, write_table

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
    ap.add_argument('stage',choices=['inspect','assembly','mapping','taxonomy','blobtoolkit','fcs'])
    ap.add_argument('--config',default='config/assembly_analysis.json')
    ap.add_argument('--force',action='store_true')
    a=ap.parse_args(); c=json.loads(path(a.config).read_text())
    if c.get('schema_version')!=1: raise ValueError('Unsupported configuration')
    os.chdir(ROOT)
    c['threads']=int(os.environ.get('OOMYCETE_THREADS',c['threads']))
    if c['threads']<1:raise ValueError('threads must be positive')
    fa=path(c['assembly']); out=path(c['output']); out.mkdir(parents=True,exist_ok=True)
    with Log('14_assembly_'+a.stage,c['sample_id'],'DNA'):
        print('CONFIG',json.dumps(c,sort_keys=True),flush=True)
        if a.stage=='inspect':
            print('Assembly:',fa,'present=',fa.is_file())
            for x in c['reads']:print('Read input:',path(x),'present=',path(x).is_file())
            for exe in ['conda','singularity','apptainer','gx','fcs.py']:print('Executable',exe,shutil.which(exe))
            print('External Kraken DB:',c['kraken_db'])
            print('FCS settings:',{k:c[k] for k in ['fcs_runner','fcs_image','fcs_db','container_engine']})
            return
        if a.stage=='assembly':
            if not fa.exists():
                from pipeline import retrieve_reference
                fa.parent.mkdir(parents=True,exist_ok=True)
                tmp=fa.with_name(fa.name+'.assembly_download.partial')
                url=retrieve_reference(c['assembly_accession'],tmp)
                list(fasta(tmp));tmp.replace(fa)
                write_json(out/'assembly_download.json',{'accession':c['assembly_accession'],'url':url,'sha256':sha(fa)})
            else:
                list(fasta(fa));print('REUSE existing assembly; see original reference retrieval metadata')
            run(['samtools','faidx',fa])
            write_json(out/'assembly_manifest.json',{'accession':c['assembly_accession'],'sample':c['sample_id'],'taxid':c['taxid'],'fasta':str(fa.relative_to(ROOT)) if fa.is_relative_to(ROOT) else str(fa),'sha256':sha(fa),'assessment_scope':'published assembly; may omit sequences present in reads'})
            return
        require_files([fa])
        bam=out/'DNA.full_cleaned.filtered.bam'
        # Depth is recomputed from read alignments; assembler header coverage is a different statistic.
        if a.stage=='mapping':
            reads=[path(x) for x in c['reads']];require_files(reads)
            with Stage(out,'assembly_mapping',[fa,*reads],c,a.force) as st:
                if st.skip:return
                t=c['threads'];raw=out/'DNA.full_cleaned.bam.partial'
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
            with Stage(out,'assembly_taxonomy',[fa],params,a.force) as st:
                if st.skip:return
                run(['kraken2','--db',db,'--threads',c['threads'],'--confidence',c['kraken_confidence'],'--report',out/'assembly.kraken.report.tsv','--output',out/'assembly.kraken.tsv',fa])
                st.complete([out/'assembly.kraken.tsv',out/'assembly.kraken.report.tsv'])
        # Import the same contig IDs into native BlobToolKit, then render browser-free R companions.
        elif a.stage=='blobtoolkit':
            inputs=[out/'samtools_coverage.tsv',out/'assembly.kraken.tsv',out/'assembly.kraken.report.tsv',fa];require_files(inputs)
            with Stage(out,'blobtoolkit',inputs,c,a.force) as st:
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
                run(['Rscript',ROOT/'scripts/assembly_blobplot.R',table,out])
                st.complete([table,*blob.glob('*.json'),out/'assembly_blobplot.png',out/'assembly_blobplot.pdf'])
        # Optional FCS screening never cleans or overwrites the assembly automatically.
        elif a.stage=='fcs':
            for key in ['fcs_runner','fcs_image','fcs_db']:
                if not c[key]:raise ValueError(f'Set {key} in {a.config}; no automatic FCS downloads')
            runner=path(c['fcs_runner']);image=path(c['fcs_image']);db=path(c['fcs_db'])
            require_files([runner,image,db/'all.gxi',db/'all.gxs',db/'all.taxa.tsv'])
            if c['container_engine']!='singularity':raise ValueError('This FCS runner requires the singularity executable; load a compatible module')
            if not shutil.which('singularity'):raise ValueError('Load the singularity module first')
            if any(any(ch.isspace() for ch in str(x)) for x in [fa,runner,image,db,out]):raise ValueError('FCS runner does not support whitespace in paths')
            params=dict(c,fcs_database_inventory=[(x.name,x.stat().st_size,x.stat().st_mtime_ns) for x in sorted(db.glob('all.*')) if x.is_file()])
            with Stage(out,'fcs_gx',[fa,runner,image],params,a.force) as st:
                if st.skip:return
                dest=out/'fcs_gx'
                if dest.exists() and any(dest.iterdir()):raise ValueError('Move incomplete/existing fcs_gx directory before retry; reports are never silently replaced')
                os.environ['FCS_DEFAULT_IMAGE']=str(image)
                os.environ['GX_NUM_CORES']=str(c['threads'])
                os.environ['SINGULARITYENV_GX_NUM_CORES']=str(c['threads'])
                run([sys.executable,runner,'screen','genome','--fasta',fa,'--out-dir',dest,'--gx-db',db,'--tax-id',c['taxid']])
                reports=list(dest.glob('*.fcs_gx_report.txt'))
                if not reports:raise RuntimeError('FCS action report missing; inspect output before marking complete')
                st.complete([*reports,*dest.glob('*.taxonomy.rpt')])

if __name__=='__main__':
    try:main()
    except Exception as error:
        print(f'ERROR {type(error).__name__}: {error}',file=sys.stderr,flush=True);sys.exit(1)
