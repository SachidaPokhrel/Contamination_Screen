#!/usr/bin/env python3
"""Independently callable analytical stages; see --help and docs/08_output_explanation.md."""
from __future__ import annotations
import argparse, collections, csv, gzip, hashlib, json, os, platform, random, re, shutil, sqlite3, subprocess, sys, tarfile, tempfile, urllib.parse, urllib.request
from pathlib import Path
from common import *

STAGES=['environment','download','qc','subsample','screen','bracken','candidates','references','mapping','coverage','viral','table','plots','report']

def params(c,a,**extra):
    """Capture the active public configuration and sample selector for provenance signatures."""
    return {'config':{k:v for k,v in c.items() if not k.startswith('_')},'sample':a.sample,**extra}
def require_files(files):
    """Fail before invoking external software when any required file is absent."""
    for f in files:
        if not Path(f).is_file():raise FileNotFoundError(f'Missing input: {f}')

def environment(c,a):
    """Inventory tools and local resources; this check does not install software."""
    required=['prefetch','fasterq-dump','vdb-validate','fastqc','fastp','seqkit','kraken2','bracken','bowtie2','bowtie2-build','samtools','minimap2','blastn','Rscript']
    records=[]
    for exe in required:
        try:v=version(exe);status='available'
        except FileNotFoundError:v='';status='missing'
        records.append({'tool':exe,'path':shutil.which(exe) or '', 'version':v,'status':status})
    write_table(ROOT/'reports/environment.tsv',records)
    mem='unknown'
    if Path('/proc/meminfo').exists():mem=Path('/proc/meminfo').read_text().splitlines()[:3]
    write_json(ROOT/'reports/environment.json',{'time':now(),'os':platform.platform(),'architecture':platform.machine(),'cpus':os.cpu_count(),'memory':mem,'disk_free_bytes':shutil.disk_usage(ROOT).free,'tools':records})
    print('Environment report: reports/environment.tsv; missing tools are reported explicitly')
    if a.strict and any(r['status']=='missing' for r in records):raise RuntimeError('Required tools missing; see reports/environment.tsv')

def download(c,a):
    """Fetch only configured runs, validate SRA, extract paired FASTQ and checksum completed files."""
    for s in samples(c,a.sample):
        with Log('01_download',s['sample_id'],'downloads'):
            runid=s['sra_run']
            if not re.fullmatch(r'[SED]RR\d+',runid):raise ValueError('A verified SRA RUN accession (SRR/ERR/DRR) is required')
            raw=read_paths(c,s,'raw');d=raw[0].parent
            require_files([path(c['datasets'])])
            versions={e:version(e) for e in ['prefetch','vdb-validate','fasterq-dump']}
            with Stage(d,s['sample_id']+'_download',[path(c['datasets'])],params(c,a,run=runid,tools=versions),a.force) as st:
                if st.skip:continue
                if not c['allow_data_download']:raise ValueError('Download disabled: approve run/size then set allow_data_download: true')
                size=int(s.get('sra_bytes') or 0)
                if size<=0:raise ValueError('sra_bytes required for disk budgeting; obtain verified archive metadata first')
                sd=path(c['data_dir'])/s['assay']/'sra';sd.mkdir(parents=True,exist_ok=True)
                scratch=path(c['scratch_dir'])/runid;scratch.mkdir(parents=True,exist_ok=True)
                reserve=size*float(c['download_reserve_factor'])+int(c['minimum_free_gb'])*1024**3
                for f in [d,scratch,sd]:
                    f.mkdir(parents=True,exist_ok=True)
                    if shutil.disk_usage(f).free<reserve:raise ValueError(f'Insufficient space at {f}; provisional budget {reserve/1024**3:.1f} GiB')
                print(f'Archive bytes={size}; provisional conversion reserve={reserve} at {scratch}')
                run(['prefetch','--max-size',c['sra_max_size'],'-O',sd,runid])
                archive=sd/runid/(runid+'.sra');require_files([archive]);run(['vdb-validate',archive])
                conv=d/(runid+'.conversion');conv.mkdir(exist_ok=True)
                run(['fasterq-dump',archive.parent,'--split-files','--threads',c['threads'],'--temp',scratch,'--outdir',conv,'--force'])
                fq=[conv/f'{runid}_{i}.fastq' for i in (1,2)];require_files(fq)
                orphan=conv/(runid+'.fastq')
                if orphan.exists() and orphan.stat().st_size:raise ValueError('Unpaired biological reads found; explicit handling required before accepting paired dataset')
                n=count_pairs(*fq)
                for source,dest in zip(fq,raw):
                    dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_name(dest.name+'.partial')
                    compressor='pigz' if shutil.which('pigz') else 'gzip'
                    args=[compressor,'-c']+(['-p',str(c['threads'])] if compressor=='pigz' else [])+[str(source)]
                    run(args,stdout=tmp);tmp.replace(dest)
                assert count_pairs(*raw)==n
                checksum=d/(s['sample_id']+'.sha256');checksum.write_text(''.join(f'{sha(f)}  {f.name}\n' for f in raw))
                manifest=ROOT/'metadata/download_manifest.tsv'
                old=table(manifest);old=[r for r in old if r['sample_id']!=s['sample_id']]
                old.extend({'sample_id':s['sample_id'],'assay':s['assay'],'run':runid,'path':portable(f),'sha256':sha(f),'bytes':f.stat().st_size,'verified_at':now()} for f in raw)
                write_table(manifest,old)
                meta=d/(s['sample_id']+'.download.json');write_json(meta,{'run':runid,'pairs':n,'reads':2*n,'archive_sha256':sha(archive),'tools':versions})
                st.complete(raw+[checksum,meta]);shutil.rmtree(conv)

def qc(c,a):
    """Run FastQC and paired fastp filtering, then verify cleaned mate counts."""
    for s in samples(c,a.sample):
        with Log('02_qc',s['sample_id'],s['assay']):
            inp=read_paths(c,s,'raw');require_files(inp);d=outdir(c,s,'01_qc');out=read_paths(c,s,'cleaned')
            for f in out:f.parent.mkdir(parents=True,exist_ok=True)
            ver={e:version(e) for e in ['fastqc','fastp']}
            with Stage(d,'qc',inp,params(c,a,tools=ver),a.force) as st:
                if st.skip:continue
                n=count_pairs(*inp);pre=d/'raw';post=d/'cleaned';pre.mkdir(exist_ok=True);post.mkdir(exist_ok=True)
                run(['fastqc','--threads',c['threads'],'--outdir',pre,*inp])
                tmp=[f.with_name(f.stem+'.partial.gz') for f in out]
                run(['fastp','--in1',inp[0],'--in2',inp[1],'--out1',tmp[0],'--out2',tmp[1],'--thread',min(16,c['threads']),'--detect_adapter_for_pe','--json',d/'fastp.json','--html',d/'fastp.html'])
                after=count_pairs(*tmp)
                for f,g in zip(tmp,out):f.replace(g)
                run(['fastqc','--threads',c['threads'],'--outdir',post,*out])
                stat=d/'pairs.json';write_json(stat,{'input_pairs':n,'cleaned_pairs':after,'cleaned_reads':after*2})
                st.complete(out+[stat,d/'fastp.json',d/'fastp.html']+list(pre.glob('*'))+list(post.glob('*')))

def subsample(c,a):
    """Select a seeded reservoir of paired fragments and write mates in consistent order."""
    for s in samples(c,a.sample):
        with Log('03_subsample',s['sample_id'],s['assay']):
            inp=read_paths(c,s,'cleaned');require_files(inp);out=read_paths(c,s,'subsampled');d=out[0].parent
            n=a.pairs or c['subsample_pairs']
            if n<1:raise ValueError('pairs must be positive')
            with Stage(d,s['sample_id']+'_subsample',inp,params(c,a,pairs=n),a.force) as st:
                if st.skip:continue
                # Two passes: choose record indices in O(n) memory; then write pairs in original order.
                total=count_pairs(*inp);rng=random.Random(c['seed']);wanted=set(rng.sample(range(total),min(n,total)))
                tmp=[f.with_name(f.stem+'.partial.gz') for f in out]
                with gzip.open(tmp[0],'wt') as f,gzip.open(tmp[1],'wt') as g:
                    for i,(x,y) in enumerate(paired(*inp)):
                        if i in wanted:f.writelines(x);g.writelines(y)
                got=count_pairs(*tmp)
                for f,g in zip(tmp,out):f.replace(g)
                meta=d/(s['sample_id']+'.subsample.json');write_json(meta,{'seed':c['seed'],'input_pairs':total,'output_pairs':got,'output_reads':2*got,'algorithm':'random.sample indices, original pair order'})
                st.complete(out+[meta])

def portable(f):
    """Record project-local paths relatively while retaining genuinely external database paths."""
    try:return str(Path(f).resolve().relative_to(ROOT))
    except ValueError:return str(Path(f).resolve())

def database(c,a):
    """Validate existing Kraken indexes or perform an explicitly permitted, budgeted download."""
    d=path(c['kraken_db']);required=[d/n for n in ['hash.k2d','opts.k2d','taxo.k2d']]
    if not all(p.is_file() and p.stat().st_size for p in required):
        if not c['allow_database_download']:raise ValueError(f'No usable Kraken2 DB at {d}. Set KRAKEN2_DB to a prepared database; downloads are opt-in')
        url=c['database_url'];n=int(c['database_archive_bytes']);expanded=int(c['database_expanded_bytes'])
        if not url.startswith('https://') or not re.fullmatch('[0-9a-f]{64}',c['database_sha256']) or min(n,expanded)<=0 or float(c['database_ram_gb'])<=0:raise ValueError('DB download requires HTTPS URL, SHA256, archive/expanded byte estimates and explicit permission')
        d.parent.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(d.parent).free<n+expanded+2*1024**3:raise ValueError('Insufficient database extraction space')
        print(f'DB budget archive={n} expanded={expanded} RAM estimate={c["database_ram_gb"]} GiB')
        archive=d.parent/'database.tar.gz.partial'
        fetch(url,archive,max_bytes=n+max(n//10,1024**2))
        if sha(archive)!=c['database_sha256']:raise ValueError('Database checksum mismatch')
        # Never execute archive paths, links or traversal entries.
        with tarfile.open(archive) as tf:
            for m in tf.getmembers():
                if m.issym() or m.islnk() or m.isdev() or not (m.isfile() or m.isdir()) or Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('Unsafe database archive entry')
            d.mkdir(exist_ok=True);tf.extractall(d,filter='data')
        archive.unlink()
    require_files(required)
    checks=ROOT/'databases'/('kraken_index_checksums_'+hashlib.sha256(portable(d).encode()).hexdigest()[:12]+'.tsv')
    write_table(checks,[{'file':portable(f),'bytes':f.stat().st_size,'sha256':sha(f)} for f in required])
    write_table(ROOT/'databases/manifest.tsv',[{'path':portable(d),'release':c['database_release'],'taxonomy_date':c['taxonomy_date'],'included_taxa':c['database_taxa'],'sha256_manifest':portable(checks),'verified_at':now()}])
    return d,required

def screen(c,a):
    """Classify paired reads with Kraken2; reports count fragments, not individual mate reads."""
    db,dbfiles=database(c,a)
    for s in samples(c,a.sample):
        with Log('04_kraken2',s['sample_id'],s['assay']):
            inp=read_paths(c,s,c['readset']);require_files(inp);d=outdir(c,s,'02_kraken2');ver=version('kraken2')
            with Stage(d,'screen',inp+dbfiles,params(c,a,version=ver),a.force) as st:
                if st.skip:continue
                n=count_pairs(*inp);rep=d/'kraken.report.tsv';out=d/'kraken.output.tsv'
                args=['kraken2','--db',db,'--threads',c['threads'],'--paired','--confidence',c['kraken_confidence'],'--report',rep,'--output',out]
                if all(str(f).endswith('.gz') for f in inp):args+=['--gzip-compressed']
                if c['kraken_memory_mapping']:args+=['--memory-mapping']
                run(args+inp)
                meta=d/'screen.json';write_json(meta,{'pairs':n,'reads':n*2,'readset':c['readset'],'db':portable(db),'release':c['database_release'],'taxonomy_date':c['taxonomy_date'],'db_taxa':c['database_taxa'],'kraken_count_unit':'paired fragments/spots for --paired'})
                st.complete([rep,out,meta])

def bracken(c,a):
    """Redistribute Kraken assignments using a distribution from the exact same database."""
    for s in samples(c,a.sample):
        with Log('05_bracken',s['sample_id'],s['assay']):
            d=outdir(c,s,'03_bracken');d.mkdir(parents=True,exist_ok=True)
            if not c['bracken_enabled']:
                write_json(d/'status.json',{'status':'disabled','reason':'requires compatible database read-length distribution; no abundance inferred'});continue
            db=path(c['kraken_db']);dist=db/f'database{c["bracken_read_length"]}mers.kmer_distrib';inp=outdir(c,s,'02_kraken2')/'kraken.report.tsv';require_files([dist,inp])
            with Stage(d,'bracken',[dist,inp],params(c,a,version=version('bracken')),a.force) as st:
                if st.skip:continue
                run(['bracken','-d',db,'-i',inp,'-o',d/'bracken.tsv','-w',d/'bracken.report.tsv','-r',c['bracken_read_length'],'-l',c['bracken_level']])
                st.complete([d/'bracken.tsv',d/'bracken.report.tsv'])

def parse_kraken(file):
    """Parse standard six-column Kraken reports while preserving clade and direct counts."""
    for line in Path(file).read_text().splitlines():
        fields=line.split('\t')
        if len(fields)<6:raise ValueError('Expected six-column standard Kraken report')
        yield {'kraken_percent':float(fields[0]),'clade_fragments':int(fields[1]),'direct_fragments':int(fields[2]),'rank':fields[3],'taxid':fields[4],'name':fields[5].strip(),'indent':len(fields[5])-len(fields[5].lstrip())}

def candidates(c,a):
    """Rank species screening hits and mark expected targets without assigning biological significance."""
    for s in samples(c,a.sample):
        with Log('06_candidates',s['sample_id'],s['assay']):
            inp=outdir(c,s,'02_kraken2')/'kraken.report.tsv';require_files([inp]);d=outdir(c,s,'04_candidates')
            with Stage(d,'candidates',[inp],params(c,a),a.force) as st:
                if st.skip:continue
                expected=set(c['expected_taxids'])|set(filter(None,s.get('expected_taxids','').split(';')))
                stack=[];rows=[]
                for r in parse_kraken(inp):
                    while stack and stack[-1][0]>=r['indent']:stack.pop()
                    target=r['taxid'] in expected or any(t in expected for _,t in stack) or r['name'] in (c['expected_names'] + [s.get('organism','')])
                    stack.append((r['indent'],r['taxid']))
                    if r['rank']!='S' or (target and c['exclude_expected']):continue
                    flags=[]
                    if target:flags.append('expected_target_or_descendant')
                    if r['clade_fragments']<c['min_candidate_reads']:flags.append('low_screening_support')
                    if not r['direct_fragments']:flags.append('descendant_only_assignment')
                    if any(w in r['name'].lower() for w in ['uncultured','unclassified','synthetic']):flags.append('uncertain_database_label')
                    rows.append({'sample_id':s['sample_id'],'assay':s['assay'],**{k:v for k,v in r.items() if k!='indent'},'expected_target':target,'flags':';'.join(flags),'interpretation':'requires independent reference validation'})
                rows.sort(key=lambda x:x['clade_fragments'],reverse=True)
                out=d/'ranked_candidates.tsv';write_table(out,rows,['sample_id','assay','taxid','name','rank','kraken_percent','clade_fragments','direct_fragments','expected_target','flags','interpretation'])
                select=d/'selection_template.tsv';write_table(select,[{'sample_id':s['sample_id'],'taxid':r['taxid'],'reference_id':'','selected':'false','note':r['name']} for r in rows],['sample_id','taxid','reference_id','selected','note'])
                st.complete([out,select]);print('Review candidates and edit config/candidate_selection.tsv before reference retrieval/mapping')

def fetch(url,dest,max_bytes=500_000_000):
    """Stream an HTTPS retrieval to disk with retry and byte-budget checks."""
    print(f'HTTP GET {url} -> {dest}',flush=True);Path(dest).parent.mkdir(parents=True,exist_ok=True)
    request=urllib.request.Request(url,headers={'User-Agent':'OomyceteEvidence/1.0 (educational bioinformatics)'})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request,timeout=60) as r,open(dest,'wb') as f:
                total=0
                while True:
                    b=r.read(1024**2)
                    if not b:break
                    total+=len(b)
                    if total>max_bytes:raise ValueError('Download exceeded configured size ceiling')
                    f.write(b)
            return
        except (OSError,urllib.error.URLError):
            if attempt==2:raise
            print(f'HTTP retry {attempt+1}',flush=True)

def references_rows(c):
    """Read and validate versioned reference configuration before retrieving sequences."""
    rows=table(path(c['references']),['reference_id','role','taxid','organism','accessions','fasta','verified'])
    seen=set()
    for r in rows:
        ident(r['reference_id'])
        if r['reference_id'] in seen:raise ValueError('Duplicate reference_id')
        seen.add(r['reference_id'])
        if r['role'] not in ('host','candidate','viral'):raise ValueError('reference role must be host/candidate/viral')
        if r['verified'].lower() not in ('true','yes','1'):raise ValueError('Reference row must be explicitly verified against NCBI or a documented local synthetic fixture')
    return rows

def selected(c,s,refs):
    """Resolve manually approved candidate references for one sample."""
    rows=table(path(c['selection']),['sample_id','taxid','reference_id','selected'])
    ids=[r['reference_id'] for r in rows if r['sample_id']==s['sample_id'] and r['selected'].lower() in ('true','yes','1')]
    if not ids:raise ValueError(f'No reviewed candidates for {s["sample_id"]}; edit config/candidate_selection.tsv after stage 06')
    by={r['reference_id']:r for r in refs}
    if len(set(ids))!=len(ids):raise ValueError('Duplicate sample/reference selection')
    if any(i not in by or by[i]['role']=='host' for i in ids):raise ValueError('Selected candidate reference missing or incorrectly labeled host')
    for r in rows:
        if r['reference_id'] in ids and r['sample_id']==s['sample_id'] and r['taxid']!=by[r['reference_id']]['taxid']:raise ValueError('Selection and reference taxids disagree')
    return [by[i] for i in ids]

def retrieve_reference(accessions,dest):
    """Resolve exact versioned NCBI accessions and retrieve genomic FASTA with cached metadata."""
    accs=accessions.split(';')
    if len(accs)==1 and re.fullmatch(r'GC[AF]_\d+\.\d+',accs[0]):
        # Resolve exact version via NCBI Assembly instead of guessing FTP hierarchy.
        base='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
        search=dest.with_name(dest.name+'.assembly_search.json')
        fetch(base+'esearch.fcgi?'+urllib.parse.urlencode({'db':'assembly','term':accs[0]+'[Assembly Accession]','retmode':'json'}),search,5_000_000)
        ids=json.loads(search.read_text())['esearchresult']['idlist']
        if len(ids)!=1:raise ValueError('Assembly accession did not resolve uniquely')
        summary=dest.with_name(dest.name+'.assembly_summary.json')
        fetch(base+'esummary.fcgi?'+urllib.parse.urlencode({'db':'assembly','id':ids[0],'retmode':'json'}),summary,5_000_000)
        record=json.loads(summary.read_text())['result'][ids[0]]
        if record['assemblyaccession']!=accs[0]:raise ValueError('NCBI returned a different assembly version')
        ftp=record.get('ftppath_genbank') or record.get('ftppath_refseq')
        if not ftp:raise ValueError('No downloadable FASTA path in assembly record')
        url=ftp.replace('ftp://','https://')+'/'+ftp.rsplit('/',1)[1]+'_genomic.fna.gz'
        zipped=dest.with_name(dest.name+'.download.gz');fetch(url,zipped,2_000_000_000)
        with gzip.open(zipped,'rb') as f,open(dest,'wb') as g:shutil.copyfileobj(f,g)
        zipped.unlink();list(fasta(dest));return url
    if not all(re.fullmatch(r'[A-Z][A-Z0-9_]*\d+\.\d+',x) for x in accs):raise ValueError('Use versioned NCBI nucleotide accessions or one versioned GCA/GCF assembly accession')
    url='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'+urllib.parse.urlencode({'db':'nuccore','id':','.join(accs),'rettype':'fasta','retmode':'text'})
    fetch(url,dest);seqs=list(fasta(dest));found={n.split('|')[-2] if '|' in n else n for n,_ in seqs}
    if not set(accs)<=found:raise ValueError('Downloaded FASTA identifiers do not match requested versioned accessions')
    return url

def references(c,a):
    """Retrieve or reuse approved references, validate FASTA, and prepare mapping indexes."""
    refs=references_rows(c);needed=set()
    for s in samples(c,a.sample):needed.update(r['reference_id'] for r in selected(c,s,refs))
    if c['competitive_mapping']:needed.update(r['reference_id'] for r in refs if r['role']=='host')
    for r in refs:
        if r['reference_id'] not in needed:continue
        with Log('07_reference',r['reference_id']):
            dest=path(r['fasta']);dest.parent.mkdir(parents=True,exist_ok=True)
            with Stage(dest.parent,r['reference_id']+'_reference',[path(c['references'])],params(c,a,ref=r),a.force) as st:
                if st.skip:continue
                if not dest.exists():
                    if not c['allow_reference_download']:raise ValueError(f'Reference missing {dest}; retrieval disabled until accession approval')
                    temp=dest.with_name(dest.name+'.partial');source_url=retrieve_reference(r['accessions'],temp);temp.replace(dest)
                    write_json(dest.with_suffix('.retrieval.json'),{'url':source_url,'accessions':r['accessions'],'time':now()})
                seqs=list(fasta(dest));meta=dest.with_suffix('.metadata.json')
                write_json(meta,{**r,'retrieved_at':now(),'sha256':sha(dest),'contigs':len(seqs),'bases':sum(len(x) for _,x in seqs),'source':'existing verified FASTA' if not r['accessions'] else 'NCBI versioned accession'})
                run(['samtools','faidx',dest]);st.complete([dest,Path(str(dest)+'.fai'),meta])

def build_combined(refs,d):
    """Concatenate references with unique contig prefixes and a reversible original-ID map."""
    fa=d/'reference.fa';rows=[]
    with open(fa,'w') as f:
        for r in refs:
            for name,seq in fasta(path(r['fasta'])):
                label=r['reference_id']+'__'+name
                f.write(f'>{label}\n{seq}\n');rows.append({'contig':label,'reference_id':r['reference_id'],'original_contig':name,'length':len(seq),'role':r['role'],'taxid':r['taxid'],'organism':r['organism']})
    write_table(d/'contigs.tsv',rows);return fa

def mapping(c,a):
    """Map exact paired inputs against candidates alone and, optionally, host plus candidates."""
    refs=references_rows(c)
    for s in samples(c,a.sample):
        choices=selected(c,s,refs);modes=[('candidate_only',choices)]
        hosts=[r for r in refs if r['role']=='host' and r.get('assay','all') in ('all','',s['assay'])]
        if c['competitive_mapping']:
            if not hosts:raise ValueError('Competitive mapping requested but no host reference configured; supply host FASTA or explicitly disable with documented limitation')
            modes.append(('competitive',hosts+choices))
        inp=read_paths(c,s,c['readset']);require_files(inp)
        for mode,rs in modes:
            with Log('08_mapping_'+mode,s['sample_id'],s['assay']):
                inputs=inp+[path(r['fasta']) for r in rs]+[path(c['references']),path(c['selection'])];require_files(inputs)
                d=outdir(c,s,'05_mapping')/mode;ver={e:version(e) for e in ['bowtie2-build','bowtie2','samtools']}
                with Stage(d,'mapping',inputs,params(c,a,mode=mode,versions=ver),a.force) as st:
                    if st.skip:continue
                    n=count_pairs(*inp);fa=build_combined(rs,d);index=d/'index'
                    run(['bowtie2-build','--threads',c['threads'],fa,index])
                    sam=d/'alignment.sam.partial'
                    # Single best alignment per read; MAPQ filtering later removes ambiguous support.
                    run(['bowtie2','--very-sensitive','--seed',c['seed'],'-p',c['threads'],'-x',index,'-1',inp[0],'-2',inp[1],'-S',sam])
                    bam=d/'aligned.bam';tmp=d/'aligned.partial.bam'
                    run(['samtools','sort','-@',max(0,c['threads']-1),'-m',c['sort_memory'],'-T',d/'sorttmp','-o',tmp,sam]);run(['samtools','quickcheck','-v',tmp]);tmp.replace(bam)
                    run(['samtools','index',bam]);run(['samtools','flagstat',bam],stdout=d/'flagstat.txt')
                    run(['samtools','stats',bam],stdout=d/'samtools.stats.txt')
                    run(['samtools','faidx',fa])
                    meta=d/'mapping.json';write_json(meta,{'sample_id':s['sample_id'],'assay':s['assay'],'readset':c['readset'],'input_pairs':n,'input_reads':n*2,'mode':mode,'tools':ver,'reference_ids':[r['reference_id'] for r in rs],'reference_warning':'RNA host competition requires transcriptome references; genomic references are not splice-aware' if s['assay']=='RNA' else ''})
                    st.complete([bam,Path(str(bam)+'.bai'),fa,Path(str(fa)+'.fai'),d/'contigs.tsv',meta,d/'flagstat.txt',d/'samtools.stats.txt']);sam.unlink()

def summarize_depth(depthfile,contigs):
    """Sum over full reference lengths; sparse or wholly absent contigs contribute zero."""
    by={r['contig']:r for r in contigs};lengths={k:int(v['length']) for k,v in by.items()}
    totals=collections.defaultdict(lambda:{'reference_length':0,'depth_sum':0,'covered_bases':0,'bases_5x':0,'bases_10x':0})
    for r in contigs:totals[r['reference_id']]['reference_length']+=int(r['length'])
    last={}
    with open_text(depthfile) as f:
        for line in f:
            if not line.strip():continue
            chrom,pos,dep=line.rstrip().split('\t');pos=int(pos);dep=int(dep)
            if chrom not in by or not 1<=pos<=lengths[chrom] or dep<0:raise ValueError('Invalid depth position, contig or value')
            if pos<=last.get(chrom,0):raise ValueError('Duplicate or unordered depth position')
            last[chrom]=pos;t=totals[by[chrom]['reference_id']];t['depth_sum']+=dep
            t['covered_bases']+=int(dep>=1);t['bases_5x']+=int(dep>=5);t['bases_10x']+=int(dep>=10)
    for t in totals.values():
        L=t['reference_length']
        if L<=0:raise ValueError('Reference length must be positive')
        t.update(mean_depth=t['depth_sum']/L,breadth_1x_percent=100*t['covered_bases']/L,breadth_5x_percent=100*t['bases_5x']/L,breadth_10x_percent=100*t['bases_10x']/L)
    return dict(totals)

def alignment_counts(sam,contigs,sqlfile):
    """Count primary aligned reads, distinct fragment names and MAPQ distributions per reference."""
    by={r['contig']:r['reference_id'] for r in contigs};counts=collections.Counter();hist=collections.defaultdict(collections.Counter)
    Path(sqlfile).unlink(missing_ok=True);db=sqlite3.connect(sqlfile)
    db.execute('create table fragments (reference text, qname text, primary key(reference,qname)) without rowid')
    with open(sam) as stream:
        for line in stream:
            if line.startswith('@'):continue
            f=line.rstrip().split('\t');ref=by[f[2]];counts[ref]+=1;hist[ref][int(f[4])]+=1
            db.execute('insert or ignore into fragments values (?,?)',(ref,f[0]))
    db.commit();fragments=dict(db.execute('select reference,count(*) from fragments group by reference'));db.close();Path(sqlfile).unlink()
    result={}
    for ref in set(by.values()):
        n=counts[ref];h=hist[ref];median=''
        if n:
            cum=0;middle=[];targets=[(n-1)//2,n//2]
            for q,k in sorted(h.items()):
                for t in targets:
                    if cum<=t<cum+k:middle.append(q)
                cum+=k
            median=sum(middle)/2
        result[ref]={'supporting_reads':n,'supporting_fragments':fragments.get(ref,0),'mean_mapq':sum(q*k for q,k in h.items())/n if n else '', 'median_mapq':median}
    return result

def coverage(c,a):
    """Apply explicit alignment filters and compute read/fragment fractions and full-reference coverage."""
    for s in samples(c,a.sample):
        base=outdir(c,s,'05_mapping');modes=['candidate_only']+(['competitive'] if c['competitive_mapping'] else [])
        for mode in modes:
            with Log('09_coverage_'+mode,s['sample_id'],s['assay']):
                src=base/mode;inputs=[src/'aligned.bam',src/'mapping.json',src/'contigs.tsv'];require_files(inputs)
                meta=json.loads(inputs[1].read_text());contigs=table(inputs[2]);d=outdir(c,s,'06_coverage')/mode
                with Stage(d,'coverage',inputs,params(c,a,version=version('samtools')),a.force) as st:
                    if st.skip:continue
                    flags=4|256|512|2048|(1024 if c['exclude_duplicates'] else 0)
                    filtered=d/'filtered.bam'
                    run(['samtools','view','-b','-q',c['min_mapq'],'-F',flags,'-e','mapq < 255','-o',filtered,inputs[0]])
                    run(['samtools','index',filtered]);run(['samtools','view',filtered],stdout=d/'support.sam')
                    counts=alignment_counts(d/'support.sam',contigs,d/'fragments.sqlite')
                    depth=d/'depth.tsv';args=['samtools','depth','-aa','-q',c['min_baseq'],'-Q',c['min_mapq']]
                    if c['depth_remove_mate_overlap']:args+=['-s']
                    if not c['exclude_duplicates']:args+=['-g','DUP']
                    run(args+['-o',depth,filtered]);metrics=summarize_depth(depth,contigs)
                    rows=[];refinfo={r['reference_id']:r for r in contigs}
                    for ref,m in metrics.items():
                        r=refinfo[ref];cnt=counts[ref]
                        if cnt['supporting_reads']>meta['input_reads']:raise ValueError('Supporting reads exceed denominator; duplicated primary alignments or wrong provenance')
                        rows.append({'sample_id':s['sample_id'],'assay':s['assay'],'reference_id':ref,'taxid':r['taxid'],'organism':r['organism'],'role':r['role'],'mapping_mode':mode,'readset':meta['readset'],**m,**cnt,'input_reads':meta['input_reads'],'input_fragments':meta['input_pairs'],'read_fraction_percent':100*cnt['supporting_reads']/meta['input_reads'],'fragment_fraction_percent':100*cnt['supporting_fragments']/meta['input_pairs'],'min_mapq':c['min_mapq'],'min_baseq':c['min_baseq'],'excluded_flags':flags,'mapq_255_excluded':True,'mate_overlap_removed_for_depth':c['depth_remove_mate_overlap'],'fragment_policy':'either_mate_per_reference','duplicate_policy':'exclude_flagged' if c['exclude_duplicates'] else 'retain','rna_reference_warning':meta.get('reference_warning','')})
                    out=d/'coverage.tsv';write_table(out,rows)
                    # Preserve compact full-depth profiles for plots; full denominators remain explicit.
                    gz=d/'depth.tsv.gz'
                    with open(depth,'rb') as f,gzip.open(gz,'wb') as g:shutil.copyfileobj(f,g)
                    filters=d/'thresholds.json';write_json(filters,{'min_mapq':c['min_mapq'],'min_baseq':c['min_baseq'],'excluded_flags':flags,'mapq255':'excluded/unavailable','depth_mate_overlap':'remove' if c['depth_remove_mate_overlap'] else 'retain','depth_deletions':'excluded','depth_refskip':'excluded','fragment_policy':'either mapped mate per reference; a discordant pair can support more than one reference, so do not sum fragment fractions across references','denominator':'all sequencing reads or paired fragments in exact input readset; not classified or mapped reads','duplicates':'only preflagged PCR/optical duplicates excluded; no duplicate marking performed'})
                    st.complete([out,gz,filters,filtered,Path(str(filtered)+'.bai')])
                    depth.unlink();(d/'support.sam').unlink()

def viral(c,a):
    """Optional reference/assembly viral extension; no completion is implied by its presence in source."""
    for s in samples(c,a.sample):
        if s['assay']!='RNA':continue
        with Log('10_viruses',s['sample_id'],'RNA'):
            modes=['candidate_only']+(['competitive'] if c['competitive_mapping'] else [])
            files=[outdir(c,s,'06_coverage')/m/'coverage.tsv' for m in modes];require_files(files)
            d=outdir(c,s,'07_viruses')
            extras=[path(c['diamond_db'])] if c['viral_discovery'] else []
            if extras:require_files(extras)
            with Stage(d,'viral',files+extras,params(c,a),a.force) as st:
                if st.skip:continue
                rows=[r for f in files for r in table(f) if r['role']=='viral']
                out=d/'reference_supported_viruses.tsv';fields=list(table(files[0])[0]) if table(files[0]) else ['sample_id','reference_id']
                write_table(out,rows,fields)
                status=d/'status.json';write_json(status,{'viral_references_evaluated':len({r['reference_id'] for r in rows}),'discovery_enabled':c['viral_discovery'],'interpretation':'mapping compatibility and coverage only; inspect ambiguity/host competition; zero rows means no viral references evaluated, not absence of viruses'})
                outputs=[out,status]
                if c['viral_discovery']:
                    inp=read_paths(c,s,c['readset']);require_files(inp)
                    assembly=d/'assembly'
                    # MEGAHIT supports continuation; isolated work directory is retained on failure.
                    args=['megahit','-1',inp[0],'-2',inp[1],'-t',c['threads'],'-o',assembly]
                    if assembly.exists():args=['megahit','--continue','-o',assembly]
                    run(args);contig=assembly/'final.contigs.fa';require_files([contig])
                    hits=d/'diamond_hits.tsv'
                    run(['diamond','blastx','--query',contig,'--db',path(c['diamond_db']),'--threads',c['threads'],'--evalue','1e-5','--sensitive','--max-target-seqs','10','--outfmt','6','qseqid','sseqid','pident','length','evalue','bitscore','qstart','qend','sstart','send','--out',hits])
                    outputs += [contig,hits]
                    print('Assembly hits are provisional. Review ORFs, RdRp motifs, nonviral homologs and host competition; add reviewed contigs as references and rerun mapping/coverage.')
                st.complete(outputs)

INTERPRET=['significance_bin','likely_source','scientific_interpretation','evidence_supporting_interpretation']
def detection_table(c,a):
    """Join screening and mapping evidence while preserving user-edited interpretation columns."""
    rows=[]
    for s in samples(c,a.sample):
        ranked=outdir(c,s,'04_candidates')/'ranked_candidates.tsv'
        screenmeta=outdir(c,s,'02_kraken2')/'screen.json'
        ranks={r['taxid']:r for r in table(ranked)} if ranked.exists() else {}
        abundance=outdir(c,s,'03_bracken')/'bracken.tsv'
        abundances={r['taxonomy_id']:r for r in table(abundance)} if c['bracken_enabled'] and abundance.exists() else {}
        screening=json.loads(screenmeta.read_text()) if screenmeta.exists() else {}
        modes=['candidate_only']+(['competitive'] if c['competitive_mapping'] else [])
        for mode in modes:
            f=outdir(c,s,'06_coverage')/mode/'coverage.tsv';require_files([f])
            for r in table(f):
                if r['role']=='host':continue
                rank=ranks.get(r['taxid'],{})
                ab=abundances.get(r['taxid'],{})
                r.update(bracken_estimated_fragments=ab.get('new_est_reads',''),bracken_fraction=ab.get('fraction_total_reads',''),bracken_read_length=c['bracken_read_length'] if ab else '')
                r.update(kraken_percent=rank.get('kraken_percent',''),kraken_clade_fragments=rank.get('clade_fragments',''),screening_flags=rank.get('flags',''),database_release=screening.get('release','unknown'),taxonomy_date=screening.get('taxonomy_date','unknown'),evidence_status='reference_alignment_evaluated')
                r.update({k:'' for k in INTERPRET});rows.append(r)
    if not rows:raise ValueError('No candidate coverage rows; run mapping/coverage first')
    # Preserve user interpretation by stable sample/reference/mode/readset key.
    dest=ROOT/'tables/detections.tsv'
    key=lambda r:tuple(r.get(k,'') for k in ['sample_id','reference_id','mapping_mode','readset'])
    previous={key(r):r for r in table(dest)} if dest.exists() else {}
    for r in rows:
        if key(r) in previous:r.update({k:previous[key(r)].get(k,'') for k in INTERPRET})
    if a.sample and previous:rows.extend(r for k,r in previous.items() if r['sample_id']!=a.sample)
    write_table(dest,rows);write_table(dest.with_suffix('.csv'),rows,delimiter=',');print(f'OUTPUT {dest} and CSV; interpretations preserved or left blank')

def report(c,a):
    """Write an editable single-detection evidence template without inventing source or significance."""
    source=ROOT/'tables/detections.tsv';require_files([source]);rows=table(source)
    if a.sample:rows=[r for r in rows if r['sample_id']==a.sample]
    if a.reference:rows=[r for r in rows if r['reference_id']==a.reference]
    if not rows:raise ValueError('No detection row matches report selection')
    # This objective ordering selects an evidence-rich template, not biological importance.
    rows.sort(key=lambda r:(r['mapping_mode']=='competitive',float(r['breadth_1x_percent']),int(r['supporting_reads'])),reverse=True);r=rows[0]
    dest=ROOT/'reports'/f"{r['sample_id']}_{r['reference_id']}_report.md"
    if dest.exists() and not a.force:raise ValueError(f'Report already exists; edit it or explicitly use --force: {dest}')
    dest.write_text(f'''# Detection evidence: {r['organism']}

Sample **{r['sample_id']}** ({r['assay']}); reference **{r['reference_id']}**, taxid {r['taxid']}; {r['mapping_mode']} mapping of {r['readset']} reads.

| Measurement | Value |
|---|---:|
| Supporting sequencing reads / input reads | {r['supporting_reads']} / {r['input_reads']} |
| Read fraction (%) | {float(r['read_fraction_percent']):.6f} |
| Supporting fragments / input pairs | {r['supporting_fragments']} / {r['input_fragments']} |
| Reference length (bp) | {r['reference_length']} |
| Mean depth (×) | {float(r['mean_depth']):.4f} |
| Breadth 1× / 5× / 10× (%) | {r['breadth_1x_percent']} / {r['breadth_5x_percent']} / {r['breadth_10x_percent']} |
| Covered reference bases | {r['covered_bases']} |
| Mean / median MAPQ | {r['mean_mapq']} / {r['median_mapq']} |

Filters: MAPQ ≥{r['min_mapq']}; base quality ≥{r['min_baseq']}; excluded flags {r['excluded_flags']}; MAPQ 255 excluded; duplicate policy {r['duplicate_policy']}; mate-overlap removal for depth {r['mate_overlap_removed_for_depth']}. Fragments use either-mate-per-reference support. Mean depth and breadth include zero-coverage reference positions. Kraken percentage is a classification statistic and is not the mapped-read fraction.

Student significance bin: **[Noise / Trace / Consequential / Biological — choose and justify]**

Likely source: **[choose from assignment categories]**

Scientific interpretation and supporting evidence: [Edit using coverage distribution, candidate-only versus competitive support, library preparation, controls, related taxa and reference provenance.]

Alternative explanations and further validation: [Inspect shared/repetitive sequence, database errors, integration, bleed-through and library chimeras. RNA coverage is expression-dependent.]

No biological source or significance has been inferred automatically. Template ordering favors competitive breadth/support and does not establish biological importance. Provenance: tables/detections.tsv; logs; configuration; reference metadata. Generated {now()}.
''')
    print(f'OUTPUT {dest}')

def plots(c,a):
    """Invoke the R evidence plots using configured result and table locations."""
    run(['Rscript',ROOT/'scripts/12_visualization.R','--config',c['_config_file'],'--table',ROOT/'tables/detections.tsv','--results',path(c['results_dir']),'--output',ROOT/'figures']+(['--force'] if a.force else []))

HANDLERS=dict(zip(STAGES,[environment,download,qc,subsample,screen,bracken,candidates,references,mapping,coverage,viral,detection_table,plots,report]))
def main(argv=None):
    """Parse this entry point and dispatch independent, restartable analysis stages with input checks."""
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=STAGES+['run','prepare-db']);p.add_argument('--config',help='Config path, relative to project root or absolute')
    p.add_argument('--sample',help='Only this enabled sample');p.add_argument('--force',action='store_true',help='Explicitly rebuild stale/completed results; report overwrite is explicit')
    p.add_argument('--pairs',type=int,help='Subsample pair count');p.add_argument('--reference',help='Reference for report template');p.add_argument('--strict',action='store_true',help='Fail environment check if dependencies missing')
    p.add_argument('--from-stage',default='download',choices=STAGES);p.add_argument('--to-stage',default='candidates',choices=STAGES,help='Default stops for candidate review')
    a=p.parse_args(argv)
    try:
        c=config(a.config)
        with Log(a.stage):
            print(f'CONFIG {c["_config_file"]} threads={c["threads"]} readset={c["readset"]}')
            if a.stage=='prepare-db':database(c,a)
            elif a.stage=='run':
                start,end=STAGES.index(a.from_stage),STAGES.index(a.to_stage)
                if end<start:raise ValueError('to-stage precedes from-stage')
                for name in STAGES[start:end+1]:
                    if name=='viral' and c['viral_discovery'] and not (shutil.which('megahit') and shutil.which('diamond')):
                        extra=(['--sample',a.sample] if a.sample else [])+(['--force'] if a.force else [])
                        run(['bash',ROOT/'hpc/environment_exec.sh','viral_analysis','bash',ROOT/'scripts/10_rna_virus_screen.sh','--config',c['_config_file'],*extra])
                    else:HANDLERS[name](c,a)
            else:HANDLERS[a.stage](c,a)
    except (Exception,KeyboardInterrupt) as e:
        print(f'ERROR {now()} {type(e).__name__}: {e}',file=sys.stderr,flush=True);return 1
    return 0
if __name__=='__main__':sys.exit(main())
