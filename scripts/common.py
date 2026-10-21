"""Portable I/O, provenance, subprocess and restart support (Python >=3.10)."""
from __future__ import annotations
import csv, gzip, hashlib, itertools, json, os, re, shlex, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def now():
    """Return an unambiguous UTC timestamp for logs and completion records."""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

def load_yaml(path):
    """Read JSON-compatible YAML directly, using PyYAML only for general YAML syntax."""
    text=Path(path).read_text()
    try: return json.loads(text)
    except json.JSONDecodeError:
        try: import yaml
        except ImportError: raise ValueError('Non-JSON YAML requires PyYAML; install environment or retain shipped JSON-compatible YAML')
        return yaml.safe_load(text)

def path(value,root=None):
    """Expand configured paths relative to the detected project root, not the caller working directory."""
    root=ROOT if root is None else root
    p=Path(os.path.expandvars(os.path.expanduser(str(value))))
    return p if p.is_absolute() else Path(root)/p

def config(file=None):
    """Load and validate runtime settings, applying documented environment overrides."""
    file=path(file or os.environ.get('OOMYCETE_CONFIG','config/config.yaml'))
    c=load_yaml(file)
    if c.get('schema_version')!=1: raise ValueError('Unsupported configuration schema_version')
    for key in ('threads','subsample_pairs'):
        if not isinstance(c.get(key),int) or c[key]<1: raise ValueError(f'{key} must be a positive integer')
    if c.get('readset') not in ('raw','cleaned','subsampled'): raise ValueError('readset must be raw, cleaned or subsampled')
    if not 0<=int(c.get('min_mapq',20))<=254: raise ValueError('min_mapq must be 0..254; MAPQ 255 is unavailable and excluded')
    if 'OOMYCETE_THREADS' in os.environ: c['threads']=int(os.environ['OOMYCETE_THREADS'])
    if c['threads']<1: raise ValueError('threads must be positive')
    if 'KRAKEN2_DB' in os.environ: c['kraken_db']=os.environ['KRAKEN2_DB']
    c['_config_file']=str(file)
    return c

def table(file,required=()):
    """Read a delimited table and require its declared schema columns."""
    with open(file,newline='') as f:
        r=csv.DictReader(f,delimiter='\t')
        if not set(required)<=set(r.fieldnames or []): raise ValueError(f'{file}: missing columns {required}')
        return list(r)

def write_table(file,rows,fields=None,delimiter='\t'):
    """Write ordered evidence rows with a header; numeric values are not interpreted biologically."""
    file=Path(file);file.parent.mkdir(parents=True,exist_ok=True)
    rows=list(rows);fields=fields or (list(rows[0]) if rows else [])
    temp=file.with_name(file.name+'.partial')
    with open(temp,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter=delimiter,extrasaction='ignore');w.writeheader();w.writerows(rows)
    temp.replace(file)

def write_json(file,obj):
    """Replace a JSON metadata file atomically after completing a temporary write."""
    file=Path(file);file.parent.mkdir(parents=True,exist_ok=True)
    tmp=file.with_name(file.name+'.partial');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(file)

def sha(file):
    """Calculate streaming SHA256 without loading the complete file into memory."""
    h=hashlib.sha256()
    with open(file,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()

def ident(value):
    """Reject unsafe sample/reference identifiers before constructing output paths."""
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',value or ''): raise ValueError(f'Unsafe identifier: {value!r}')
    return value

def samples(c,sample=None):
    """Select enabled DNA/RNA samples from metadata and enforce unique safe identifiers."""
    rows=table(path(c['datasets']),['sample_id','assay','raw_r1','raw_r2','sra_run','enabled'])
    rows=[s for s in rows if s['enabled'].lower() in ('true','1','yes')]
    if sample: rows=[s for s in rows if s['sample_id']==sample]
    if not rows: raise ValueError('No enabled samples match; populate config/datasets.tsv or run the synthetic test')
    seen=set()
    for s in rows:
        ident(s['sample_id'])
        if s['sample_id'] in seen: raise ValueError('Duplicate sample_id')
        seen.add(s['sample_id'])
        if s['assay'] not in ('DNA','RNA'): raise ValueError('assay must be DNA or RNA')
    return rows

def read_paths(c,s,kind):
    """Resolve the two mates for a configured raw, cleaned or subsampled input readset."""
    if kind=='raw' and s['raw_r1'] and s['raw_r2']: return [path(s['raw_r1']),path(s['raw_r2'])]
    d=path(c['data_dir'])/s['assay']/kind
    return [d/f"{s['sample_id']}_{i}.fastq.gz" for i in (1,2)]

def outdir(c,s,stage):
    """Resolve the assay/stage/sample output directory without hardcoded project locations."""
    return path(c['results_dir'])/s['assay']/stage/s['sample_id']

def open_text(file,mode='rt'):
    """Open plain or gzip-compressed sequence input using the matching reader."""
    return gzip.open(file,mode) if str(file).endswith('.gz') else open(file,mode)

def fastq(file):
    """Yield validated four-line FASTQ records and reject truncation or inconsistent quality lengths."""
    with open_text(file) as f:
        while True:
            rec=tuple(f.readline() for _ in range(4))
            if not rec[0]:
                if any(rec): raise ValueError(f'{file}: invalid trailing FASTQ content')
                return
            if not all(rec) or not rec[0].startswith('@') or not rec[2].startswith('+') or len(rec[1].rstrip())!=len(rec[3].rstrip()) or not rec[1].strip():
                raise ValueError(f'{file}: truncated/invalid FASTQ')
            yield rec

def mate_id(rec):
    """Normalize a FASTQ identifier by removing only the terminal mate suffix."""
    return re.sub(r'/[12]$','',rec[0][1:].split()[0])

def paired(r1,r2):
    """Yield synchronized mate records, requiring matching identifiers and equal record counts."""
    for a,b in itertools.zip_longest(fastq(r1),fastq(r2)):
        if a is None or b is None or mate_id(a)!=mate_id(b): raise ValueError('FASTQ mate counts or identifiers disagree')
        yield a,b

def count_pairs(r1,r2):
    """Count validated paired fragments; an empty readset is a critical input error."""
    n=sum(1 for _ in paired(r1,r2))
    if n==0: raise ValueError('Empty paired FASTQ')
    return n

def fasta(file):
    """Yield unique nucleotide FASTA identifiers and sequences while rejecting malformed records."""
    name=None;seq=[];seen=set()
    with open_text(file) as f:
        for line in f:
            if line.startswith('>'):
                if name is not None:
                    if not seq: raise ValueError('Empty FASTA sequence')
                    yield name,''.join(seq)
                name=line[1:].split()[0];seq=[]
                if name in seen: raise ValueError(f'Duplicate FASTA id {name}')
                seen.add(name)
            elif line.strip():
                if name is None or not re.fullmatch('[ACGTURYSWKMBDHVNacgturyswkmbdhvn]+',line.strip()): raise ValueError('Invalid nucleotide FASTA')
                seq.append(line.strip().upper())
    if name is None or not seq: raise ValueError(f'Empty or invalid FASTA: {file}')
    yield name,''.join(seq)

class Tee:
    """Mirror log writes immediately to console and file."""
    def __init__(self,*files): self.files=files
    def write(self,s):
        for f in self.files: f.write(s);f.flush()
    def flush(self):
        for f in self.files: f.flush()

class Log:
    """Record start, finish and exceptions without suppressing analysis failures."""
    def __init__(self,stage,sample='pipeline',assay=''):
        # Synthetic fixtures must not append to the biological execution history.
        base = ROOT/'logs/verification/synthetic' if 'SYNTHETIC' in sample else ROOT/'logs'/assay
        self.file=base/f'{stage}_{sample}.log';self.file.parent.mkdir(parents=True,exist_ok=True)
    def __enter__(self):
        self.fp=open(self.file,'a',buffering=1);self.old=(sys.stdout,sys.stderr)
        sys.stdout=Tee(self.old[0],self.fp);sys.stderr=Tee(self.old[1],self.fp)
        print(f'\nSTART {now()} pid={os.getpid()} python={sys.version.split()[0]} log={self.file}',flush=True)
        return self
    def __exit__(self,t,v,tb):
        print(f'FINISH {now()} exit_status={0 if t is None else 1}'+(f' error={v}' if v else ''),flush=True)
        sys.stdout,sys.stderr=self.old;self.fp.close()

VERSIONS={}
def version(exe):
    """Record tool-specific version commands once per process, retaining errors as explicit metadata."""
    if exe in VERSIONS:return VERSIONS[exe]
    if not shutil.which(exe): raise FileNotFoundError(f'Required executable missing: {exe}; run hpc/install_hpc_environment.sh')
    args={'seqkit':['version'],'fastqc':['--version'],'bracken':['-v','1'],'blastn':['-version'],'prefetch':['--version'],'fasterq-dump':['--version'],'vdb-validate':['--version']}.get(exe,['--version'])
    p=subprocess.run([exe]+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    v=' | '.join(p.stdout.strip().splitlines()[:3]) or f'version query exit {p.returncode}'
    VERSIONS[exe]=v;print(f'VERSION {exe}: {v}',flush=True);return v

def run(args,stdout=None):
    """Execute argument lists without shell interpolation and stream stdout/stderr into live logs."""
    args=[str(a) for a in args];version(args[0]);print(f'COMMAND {now()} {shlex.join(args)}'+(f' > {stdout}' if stdout else ''),flush=True)
    # stderr always streams immediately; stdout can be a binary artifact.
    dest=open(stdout,'wb') if stdout else None
    try:
        p=subprocess.Popen(args,stdout=dest or subprocess.PIPE,stderr=subprocess.PIPE,text=False)
        import threading
        def drain(stream,target):
            for b in iter(stream.readline,b''): target.write(b.decode(errors='replace'));target.flush()
        th=threading.Thread(target=drain,args=(p.stderr,sys.stderr));th.start()
        if not dest: drain(p.stdout,sys.stdout)
        rc=p.wait();th.join()
        if rc: raise RuntimeError(f'{args[0]} failed with exit status {rc}')
    finally:
        if dest:dest.close()

def portable(file):
    """Record project-local paths relatively while retaining genuinely external database paths."""
    try: return str(Path(file).resolve().relative_to(ROOT))
    except ValueError: return str(Path(file).resolve())

def signature(inputs,params):
    """Hash source, input content and parameters to detect changed or stale stage outputs."""
    values={'params':params,'code':{str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'scripts').glob('*.py')},'inputs':{portable(p):sha(p) for p in inputs}}
    return hashlib.sha256(json.dumps(values,sort_keys=True).encode()).hexdigest()

class Stage:
    """Guard a stage with a lock and verify parameter/input signatures plus output checksums."""
    def __init__(self,directory,name,inputs,params,force=False):
        self.d=Path(directory);self.d.mkdir(parents=True,exist_ok=True);self.state=self.d/(name+'.done.json')
        self.sig=signature(inputs,params);self.force=force;self.skip=False
    def __enter__(self):
        self.lock=self.state.with_suffix('.lock')
        try:self.fd=os.open(self.lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        except FileExistsError:raise RuntimeError(f'Stage locked: {self.lock}; inspect running jobs before removing a stale lock')
        os.write(self.fd,str(os.getpid()).encode())
        try:
            if self.state.exists():
                s=json.loads(self.state.read_text())
                valid=s['signature']==self.sig and all(path(p).exists() and sha(path(p))==v for p,v in s['outputs'].items())
                if valid and not self.force:self.skip=True;print(f'SKIP verified {self.state}',flush=True)
                elif not self.force:raise RuntimeError(f'Stale/modified outputs: {self.state}; inspect and use --force to rebuild')
            if not self.skip and self.state.exists():self.state.unlink()
            return self
        except BaseException:
            os.close(self.fd);self.lock.unlink(missing_ok=True);raise
    def complete(self,outputs):
        if not outputs:raise ValueError('Cannot complete stage without outputs')
        write_json(self.state,{'signature':self.sig,'outputs':{portable(p):sha(p) for p in outputs},'finished':now()})
        print('OUTPUTS '+', '.join(str(p) for p in outputs),flush=True)
    def __exit__(self,*exc):os.close(self.fd);self.lock.unlink(missing_ok=True)
