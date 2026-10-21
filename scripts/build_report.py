#!/usr/bin/env python3
"""Build an offline HTML results report and summary tables from retained HPC evidence.

No aligner, assembler, classifier, network service, or scientific significance
classifier is invoked. Original detection measurements and user interpretation
columns are never overwritten. All displayed figures are embedded as data URIs.
"""
import argparse
import base64
from collections import Counter, defaultdict
import csv
import datetime as dt
import html
import json
from pathlib import Path
import re
from fcs_analysis import write_summaries

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = [('DNA', 'DNA_Gokan_CBS315_81'), ('RNA', 'RNA_Phib_mycelia1')]
BRANCHES = [
    ('Published DNA assembly', 'results/DNA/07_assembly/DNA_Gokan_CBS315_81', 'assembly_blobplot.png'),
    ('De novo DNA assembly', 'results/DNA/08_denovo/DNA_Gokan_CBS315_81', 'dna_denovo_blobplot.png'),
    ('De novo RNA transcriptome', 'results/RNA/08_transcriptome/RNA_Phib_mycelia1', 'rna_blobplot.png'),
]


def read_tsv(relative):
    """Read retained evidence without inferring meaning from taxonomic labels."""
    with (ROOT / relative).open(newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def write_tsv(relative, rows):
    """Write a derived, explicitly named summary; never replace primary detections."""
    if not rows:
        return
    with (ROOT / relative).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def esc(value):
    return html.escape(str(value))


def table(rows, columns, searchable=False):
    """Render escaped cells with column labels; preserve blanks as unresolved."""
    headers = ''.join(f'<th scope="col">{esc(label)}</th>' for _, label in columns)
    body = ''.join('<tr>' + ''.join(f'<td>{esc(row.get(key, ""))}</td>' for key, _ in columns) + '</tr>' for row in rows)
    return f'<div class="table-wrap"><table class="{"searchable" if searchable else ""}"><thead><tr>{headers}</tr></thead><tbody>{body}</tbody></table></div>'


def figure(relative, title, caption):
    """Embed the actual retained PNG; no network or companion image files are needed."""
    image = ROOT / relative
    encoded = base64.b64encode(image.read_bytes()).decode('ascii')
    return f'<figure><h3>{esc(title)}</h3><img loading="lazy" src="data:image/png;base64,{encoded}" alt="{esc(title)}"><figcaption>{esc(caption)} Source: <a href="{esc(relative)}">{esc(relative)}</a>.</figcaption></figure>'


def collect_history():
    """Extract timestamped run blocks, including failed attempts, from original stage logs."""
    events = []
    sources = [*(ROOT / 'logs/DNA').glob('*.log'), *(ROOT / 'logs/RNA').glob('*.log'), *(ROOT / 'logs/downloads').glob('*.log')]
    for source in sources:
        if 'SYNTHETIC' in source.name:
            continue
        text = source.read_text(errors='replace')
        for match in re.finditer(r'^START (\S+)(.*?)(?=^START |\Z)', text, re.M | re.S):
            stamp, block = match.groups()
            finish = re.findall(r'^FINISH (\S+) exit_status=(\d+)', block, re.M)
            events.append(dict(start_utc=stamp, finish_utc=finish[-1][0] if finish else '', status=('PASS' if finish[-1][1] == '0' else 'FAILED_ATTEMPT') if finish else 'NO_FINISH_RECORDED', step=source.stem, evidence=str(source.relative_to(ROOT))))
    events.sort(key=lambda row: (row['start_utc'], row['step']))
    write_tsv('provenance/run_history.tsv', events)
    return events


def collect():
    """Derive QC, screening, assembly and abundance summaries from primary artifacts."""
    qc, screens, bracken, assemblies, taxa = [], [], [], [], []
    for assay, sample in SAMPLES:
        pairs = json.loads((ROOT / f'results/{assay}/01_qc/{sample}/pairs.json').read_text())
        fastp = json.loads((ROOT / f'results/{assay}/01_qc/{sample}/fastp.json').read_text())['summary']
        qc.append(dict(assay=assay, sample_id=sample, input_pairs=pairs['input_pairs'], cleaned_pairs=pairs['cleaned_pairs'], retained_pairs_percent=round(100 * pairs['cleaned_pairs'] / pairs['input_pairs'], 4), q30_after_percent=round(100 * fastp['after_filtering']['q30_rate'], 3), input_scope='full readset'))
        for base, label in [('results', 'Original database'), ('results_pluspf', 'pluspf comparison')]:
            report = f'{base}/{assay}/02_kraken2/{sample}/kraken.report.tsv'
            meta = json.loads((ROOT / f'{base}/{assay}/02_kraken2/{sample}/screen.json').read_text())
            counts = {}
            for line in (ROOT / report).read_text().splitlines():
                fields = line.split('\t')
                if fields[3] in ['U', 'R']:
                    counts[fields[3]] = int(fields[1])
            screens.append(dict(assay=assay, database=label, input_pairs=meta['pairs'], classified_pairs=counts.get('R', 0), unclassified_pairs=counts.get('U', 0), classified_percent=round(100 * counts.get('R', 0) / meta['pairs'], 4), source=report))
        distribution = 150 if assay == 'DNA' else 100
        for row in read_tsv(f'results_pluspf/{assay}/03_bracken/{sample}/bracken.tsv'):
            bracken.append(dict(assay=assay, sample_id=sample, name=row['name'], taxid=row['taxonomy_id'], directly_assigned_fragments=int(row['kraken_assigned_reads']), redistributed_fragments=int(row['added_reads']), estimated_fragments=int(row['new_est_reads']), bracken_model_percent=round(100 * float(row['fraction_total_reads']), 4), estimated_input_pair_percent=round(100 * int(row['new_est_reads']) / 100000, 4), input_pairs=100000, distribution_bp=distribution, validation_status='screening_estimate_not_independent_confirmation'))
    for label, base, image in BRANCHES:
        rows = read_tsv(base + '/contig_evidence.tsv')
        lengths = sorted((int(row['length']) for row in rows), reverse=True)
        total = sum(lengths)
        cumulative = 0
        for length in lengths:
            cumulative += length
            if cumulative >= total / 2:
                n50 = length
                break
        unclassified = sum(int(row['length']) for row in rows if row['kraken_taxid'] == '0')
        assemblies.append(dict(branch=label, sequences=len(rows), total_bases=total, N50_bp=n50, longest_bp=max(lengths), unclassified_bases_percent=round(100 * unclassified / total, 5), input_scope='published assembly + full cleaned DNA mapping' if label.startswith('Published') else 'full cleaned reads assembled de novo', source=base + '/contig_evidence.tsv'))
        groups = defaultdict(list)
        for row in rows:
            groups[row['kraken_label']].append(row)
        for taxon, records in sorted(groups.items(), key=lambda item: sum(int(row['length']) for row in item[1]), reverse=True):
            bases = sum(int(row['length']) for row in records)
            taxa.append(dict(branch=label, assigned_label=taxon.replace('_', ' '), sequences=len(records), bases=bases, assembly_bases_percent=round(100 * bases / total, 5), length_weighted_mean_depth=round(sum(int(row['length']) * float(row['mean_depth']) for row in records) / bases, 5), interpretation='provisional whole-contig assignment'))
    write_tsv('tables/qc_summary.tsv', qc)
    write_tsv('tables/screening_summary.tsv', screens)
    write_tsv('tables/bracken_comparison.tsv', bracken)
    write_tsv('tables/assembly_summary.tsv', assemblies)
    write_tsv('tables/assembly_taxonomy_summary.tsv', taxa)
    return dict(qc=qc, screens=screens, bracken=bracken, assemblies=assemblies, taxa=taxa)


def build():
    """Write a self-contained narrative report with transparent scientific limitations."""
    data = collect()
    fcs = write_summaries(json.loads((ROOT / "fcs/config.json").read_text()))
    data["fcs"] = fcs
    history = collect_history()
    detections = read_tsv('tables/detections.tsv')
    audit = read_tsv('tables/pseudomonas_rrna_alignment_audit.tsv')
    audits = Counter((row['sample_id'], row['category']) for row in audit)
    display = []
    for row in detections:
        display.append(dict(sample=row['assay'], reference=row['reference_id'], mode=row['mapping_mode'], reads=row['supporting_reads'], fragments=row['supporting_fragments'], read_percent=f"{float(row['read_fraction_percent']):.4f}", depth=f"{float(row['mean_depth']):.6f}", reference_bases=row['reference_length'], covered_bases=row['covered_bases'], mean_mapq=row['mean_mapq'], median_mapq=row['median_mapq'], breadth=f"{float(row['breadth_1x_percent']):.5f}", breadth5=f"{float(row['breadth_5x_percent']):.5f}", breadth10=f"{float(row['breadth_10x_percent']):.5f}", significance=row['significance_bin'] or 'Unassigned', source=row['likely_source'] or 'Unassigned'))
    status = [
        ('Read QC, subsampling, screening and candidate mapping', 'Completed on HPC', 'Original logs and retained coverage tables'),
        ('Separate pluspf Kraken2–Bracken comparison', 'Completed on HPC', '11 species-level estimate rows across DNA and RNA'),
        ('Published DNA assembly BlobToolKit analysis', 'Completed on HPC', 'Native BlobDir + R-rendered blobplot'),
        ('De novo DNA SPAdes + BlobToolKit', 'Completed on HPC', 'Contigs, manifest, native BlobDir + R blobplot'),
        ('RNA rnaSPAdes + BlobToolKit', 'Completed on HPC', 'Transcripts, manifest, native BlobDir + R blobplot'),
        ('FCS-GX: independent G. irregulare public genome', 'Completed on HPC; supplied outputs audited locally', '8 full-contig EXCLUDE actions; original DNA/RNA assembly branches have no completed FCS report'),
        ('Virus-specific protein similarity / viral validation', 'Not performed in retained evidence', 'Transcript assembly alone is not virus discovery'),
        ('Significance bins and likely sources', 'User decisions pending', 'Original table columns remain editable and unassigned'),
    ]
    sections = []
    def section(id, title, content):
        sections.append(f'<section id="{id}"><div class="section-label">{len(sections)+1:02d}</div><h2>{title}</h2>{content}</section>')
    section('overview', 'What was done—and what the evidence supports', '<p class="lead">Two independent oomycete datasets were screened for non-target sequences, followed by reference mapping, targeted specificity checks, and assembly-based visualisation. The completed runs include both <strong>de novo DNA assembly</strong> and <strong>de novo RNA transcript assembly</strong>.</p><div class="callout"><strong>Main finding:</strong> the pilot Pseudomonas CIP-10 assignment was not independently validated. Its retained support was dominated by structural RNA regions; broader searches offered oomycete/eukaryotic alternatives. This does not prove every read is host-derived, nor establish a database error.</div>' + table([dict(stage=a,status=b,evidence=c) for a,b,c in status], [('stage','Analysis'),('status','Observed status'),('evidence','Evidence / limitation')]))
    section('samples', 'Two samples, two case studies', '<p>These are <strong>different species and isolates</strong>, not matched DNA and RNA from one organism. Shared screening labels cannot demonstrate a shared infection or associate.</p>' + table([dict(assay='DNA WGS',organism='Globisporangium okanoganense CBS 315.81',run='SRR15309490',sample='SAMN13878593',project='PRJNA601986',platform='Illumina NextSeq 500; paired; nominal 151 bp'),dict(assay='RNA-seq',organism='Phytophthora hibernalis; Phibe_mycelia1',run='SRR16206986',sample='SAMN22065162',project='PRJNA746351',platform='Illumina HiSeq 2000; paired; nominal 90 bp')], [('assay','Readset'),('organism','Organism / sample'),('run','SRA run'),('sample','BioSample'),('project','BioProject'),('platform','Platform')]) + '<p>Both are cultured isolates; original field source and RNA-virus infection were not established. The published DNA assembly GCA_023334035.1 shares the DNA BioSample; RNA host genome GCA_024679025.1 is the same species, with isolate identity unconfirmed.</p>' + table(data['qc'], [('assay','Assay'),('input_pairs','Downloaded pairs'),('cleaned_pairs','Cleaned pairs'),('retained_pairs_percent','Pairs retained (%)'),('q30_after_percent','Q30 after QC (%)')]) + '<p class="source">Sources: <a href="metadata/selected_datasets.tsv">selected metadata</a>; original fastp JSON and pairs.json under results/*/01_qc/. Raw/cleaned readsets are intentionally absent from this repository.</p>')
    sections[-1] = sections[-1].replace('</section>', '<h3>Additional assembly-only dataset</h3><p><strong>Globisporangium irregulare strain 13-30, GCA_051997085.1</strong>; PRJNA816194; SAMN26664723; WGS JALBZS000000000; taxid 36331. Input: 5,451 sequences, 42,653,821 bp. Selected because the user reports NCBI flagged the genome as contaminated; exact flag wording was not independently retrieved. This independent FCS-GX case is not either SRA readset above. No associated SRA run was verified and no raw reads from this genome were analysed. See the FCS-GX case section for findings and <a href="metadata/analysis_datasets.tsv">all dataset metadata</a>.</p></section>')
    section('workflow', 'Analysis flow', '''<div class="flow"><div>SRA runs<br><small>prefetch → validation → paired FASTQ</small></div><b>↓</b><div>FastQC + fastp<br><small>full cleaned paired readsets</small></div><b>↓</b><div>100,000 pairs per sample<br><small>seed 1729 → Kraken2 → candidate review</small></div><b>↓</b><div>Candidate-only and competitive mapping<br><small>Bowtie2 + SAMtools → read fraction, depth, breadth</small></div><b>↓</b><div>Specificity audit<br><small>rRNA/tRNA annotations + selected-pair NCBI BLAST</small></div></div><div class="branch-grid"><div><h3>Parallel abundance comparison</h3><p>Same subsamples → pluspf Kraken2 → Bracken (DNA 150 bp; RNA 100 bp approximation).</p></div><div><h3>Assembly branches</h3><p>Published DNA genome + full DNA reads; SPAdes DNA contigs; rnaSPAdes transcripts → read mapping + contig Kraken labels → native BlobToolKit data and R figures.</p></div></div><p>Genome assembly and transcript assembly used the <strong>full cleaned reads</strong>, not the screening subsamples. RNA strandedness was left unknown rather than guessed. Assembly coverage is mapped per-base depth, not the k-mer coverage printed in SPAdes headers.</p>''')
    section('screening', 'Read screening and database dependence', table(data['screens'], [('assay','Assay'),('database','Database branch'),('input_pairs','Input pairs'),('classified_pairs','Classified pairs'),('unclassified_pairs','Unclassified pairs'),('classified_percent','Classified (%)')]) + '<p>Kraken2 was run with confidence 0.1. Paired classification counts represent fragments/spots. Most reads were unclassified against these databases; this alone does not establish their biological origin or prove target-genome absence from an index.</p><p>The original database and pluspf are distinct. The much larger nt_database index was <strong>not</strong> used. Database release/taxonomy provenance remain unknown where records do not establish them. No new database was downloaded.</p>')
    section('mapping', 'Candidate validation: measured evidence', '<p>These are the retained final mapping measurements. The denominator is <strong>200,000 sequencing reads or 100,000 paired fragments per sample</strong>, not classified reads. References are representative genomes; zero support against one reference does not exclude every strain or member of that group.</p><label class="search-label">Filter detection rows <input id="filter" type="search" placeholder="Sample, reference, mapping mode…"></label>' + table(display, [('sample','Assay'),('reference','Reference'),('mode','Mapping mode'),('reads','Reads'),('fragments','Fragments'),('read_percent','Input reads (%)'),('depth','Mean depth (×)'),('reference_bases','Reference bases'),('covered_bases','Covered bases'),('mean_mapq','Mean MAPQ'),('median_mapq','Median MAPQ'),('breadth','Breadth ≥1× (%)'),('breadth5','≥5× (%)'),('breadth10','≥10× (%)'),('significance','Significance bin'),('source','Likely source')], True) + '<p>Candidate filters: MAPQ ≥20; unavailable MAPQ255 excluded; primary, non-QC-failed, non-flagged-duplicate alignments; base quality ≥0. Depth removes overlapping mates and includes zero-depth positions across all reference contigs. No duplicate marking was performed. Fragments count distinct read-pair names with either mate supporting a reference; do not sum across discordant reference assignments. RNA host competition used a genomic reference, so splice-spanning reads are a limitation.</p><p class="source"><a href="tables/detections.tsv">Full TSV</a> · <a href="tables/detections.csv">CSV</a> · <a href="tables/README.md">Column definitions</a>. RNA round-two measurements replace the earlier pilot rows in the final table; earlier runs remain separately retained.</p>')
    section('specificity', 'Why the Pseudomonas pilot was not validated', table([dict(assay='DNA',reads=143,fragments=116,rrna=audits[('DNA_Gokan_CBS315_81','annotated_rRNA_overlap')],other='0 outside annotated rRNA'),dict(assay='RNA',reads=128,fragments=115,rrna=audits[('RNA_Phib_mycelia1','annotated_rRNA_overlap')],other='1 tRNA-overlapping read; 1 sucD read')], [('assay','Assay'),('reads','Competitive reads'),('fragments','Supporting fragments'),('rrna','rRNA-overlapping reads'),('other','Remaining support')]) + '<p>The rRNA-overlapping alignments fall on CP087163.1, an 8,012 bp record labelled plasmid unnamed3 with annotated 16S, 23S, 5S and partial 16S features. Annotation overlap does not mean every base of a read lies within that feature. The label alone does not establish a genuine plasmid or a database error.</p><p>The remaining RNA chromosome alignments overlapped tRNA-Gln and sucD. Both mates of the sucD pair matched <em>Phytophthora</em> transcripts; the displayed mate-1 hits included 93.33% identity across 90 bp, and mate 2 matched 64/90 bp at 93.75% identity. Representative rRNA pairs matched oomycete and other eukaryotic references at high identity, often across the full read. Short conserved matches labelled plant, moss or other taxa are not independent evidence that those organisms contaminated the sample.</p><p><strong>Conclusion at the claimed species level:</strong> species-specific Pseudomonas CIP-10 support was not demonstrated. This remains an objective evidence conclusion, not an assigned significance bin or contamination-source category.</p><p>Other pilot results: Acetobacteroides and Tateyamaria had zero retained support against the selected references. Stenotrophomonas had zero retained support in round two. Miltoncostaea retained 11 competitive RNA reads covering only 130 reference bases, each 90 bp alignment with 7–11 edit differences. Its subsequent interval BLAST was skipped and is not presented as completed.</p><p class="source"><a href="reports/pseudomonas_specificity_review.md">Specificity evidence</a> · <a href="tables/pseudomonas_rrna_alignment_audit.tsv">Per-alignment audit</a> · <a href="tables/rrna_specificity_review/nt_results.tsv">Representative-pair BLAST</a> · <a href="results/RNA/08_specificity_review/RNA_Phib_mycelia1/sucD_pair_nt_retry.tsv">sucD-pair BLAST</a>.</p>')
    section('bracken', 'Bracken: estimates, not mapping confirmation', '<div class="callout"><strong>Two denominators:</strong> the reported Bracken fraction is normalized within its estimated species-level pool. It is not the fraction of all input pairs. The separate input-pair percentage below is estimated fragments ÷100,000×100.</div>' + table(data['bracken'], [('assay','Assay'),('name','Assigned species'),('directly_assigned_fragments','Direct assignments'),('redistributed_fragments','Redistributed'),('estimated_fragments','Estimated fragments'),('bracken_model_percent','Bracken model (%)'),('estimated_input_pair_percent','All input pairs (%)'),('distribution_bp','Model length (bp)')]) + '<p>Bracken ran against the matching pluspf distributions, not distributions from the different nt_database index. DNA averaged about149 bp after trimming; 150 bp is a close model. RNA was predominantly90 bp, so the 100 bp distribution is an approximation. Assignments such as Bremia, human and fungi remain unvalidated estimates. RNA estimates also reflect expression and library preparation; they are not cell-abundance estimates. Original candidate-mapping measurements are not replaced by these estimates.</p><p class="source"><a href="tables/bracken_comparison.tsv">Derived comparison with explicit denominators</a>; original output under results_pluspf/. Bracken implementation: <a href="https://github.com/jenniferlu717/Bracken/blob/master/src/est_abundance.py">normalization code</a>.</p>')
    section('assemblies', 'Assemblies actually analysed', table(data['assemblies'], [('branch','Branch'),('sequences','Contigs / transcripts'),('total_bases','Total bases'),('N50_bp','N50 (bp)'),('longest_bp','Longest (bp)'),('unclassified_bases_percent','Unclassified bases (%)')]) + '<p>The DNA SPAdes run used 5,685,476 cleaned pairs; RNA rnaSPAdes used 5,941,455 cleaned pairs. SPAdes4.2.0 is recorded in HPC logs. DNA assembly was not guided by the published reference. N50 is descriptive and does not establish correctness, completeness or contamination status.</p><p>Contig classification is overwhelmingly unclassified. Human-labelled DNA contigs and Bremia-labelled DNA/RNA sequences are provisional observations; no species-specific assembly validation has been performed for those labels. The DNA de novo assembly and the published assembly differ in size and fragmentation; differences can reflect assembly and curation rather than contamination.</p><p>Assembly depth retains MAPQ≥20 primary alignments. Unlike candidate depth, overlapping mates can both contribute. Repeated or shared transcript isoforms may lose support under this filter. RNA depth reflects expression, not genomic copy number. Contig taxonomy labels do not locate internal chimeric segments.</p>' + table([row for row in data['taxa'] if row['assigned_label']!='unclassified'], [('branch','Branch'),('assigned_label','Provisional label'),('sequences','Sequences'),('bases','Bases'),('assembly_bases_percent','Assembly bases (%)'),('length_weighted_mean_depth','Length-weighted depth')]) + '<p class="source"><a href="tables/assembly_summary.tsv">Assembly summary</a> · <a href="tables/assembly_taxonomy_summary.tsv">All contig-label aggregates</a>. Final de novo FASTAs are retained losslessly as gzip, with restoration checksums in metadata/retained_assemblies.json.</p>')
    blob_html = ''
    for label, base, image in BRANCHES:
        blob_html += figure(base + '/' + image, label, 'Actual HPC-generated static figure. X: GC fraction; Y: retained mean read depth +0.001 on a logarithmic scale; point area: sequence length; colour: provisional Kraken whole-contig assignment. Static rendering uses R; the native BlobToolKit dataset is retained alongside it.' + (' RNA depth is expression-dependent.' if 'RNA' in label else ''))
    section('blobplots', 'Embedded blobplots', blob_html)
    figs = ''
    for name, title in [('read_fractions','Candidate mapped-read fractions'),('breadth_vs_depth','Breadth versus depth'),('coverage_profiles','Candidate coverage profiles'),('taxonomic_screening','Original screening assignments')]:
        relative = f'figures/final/{name}.png'
        if (ROOT / relative).exists():
            figs += figure(relative, title, 'Retained final HPC export. Candidate-only and competitive measurements are distinct; the absence of a coloured or high-abundance signal is not proof of organism absence.')
    section('figures', 'Other final evidence figures', figs)
    section('history', 'Recorded sequence of events', '<p>Timestamps below come from retained stage logs and are shown in UTC. Failed attempts remain visible; their presence does not invalidate later successful runs. This is an execution history, not a fabricated chat transcript.</p>' + table(history, [('start_utc','Started (UTC)'),('finish_utc','Finished (UTC)'),('step','Stage / sample'),('status','Recorded outcome')]) + '<p class="source"><a href="provenance/run_history.tsv">Full event table with log paths</a> · <a href="agent/execution_log.md">Agent execution record</a> · <a href="agent/transcript.md">Transcript availability</a>.</p>')
    section('fcs', 'Independent public-genome FCS-GX case', '<p><strong>Globisporangium irregulare strain 13-30</strong>, assembly GCA_051997085.1; BioProject PRJNA816194; BioSample SAMN26664723; WGS master JALBZS000000000. This is a third, assembly-only case, distinct from both original SRA readsets. No associated SRA run accession was verified; this does not establish that no reads are available.</p><div class="callout"><strong>Selection rationale:</strong> the user reports that NCBI flagged this genome as contaminated. The exact current flag wording was not independently retrieved. This is a deliberately selected, previously flagged case, not a blind discovery or a detection-limit experiment.</div><p>The supplied FCS-GX v0.5.0 action report classifies eight complete contigs as fungal Ascomycetes and recommends EXCLUDE. They total <strong>12,358 bp, or 0.028973% of the 42,653,821 bp input assembly</strong>. The retained output has 5,443 sequences and 42,641,463 bp, versus 5,451 input sequences. Top taxon labels are provisional similarity assignments, not proof of living fungal associates or a particular contamination route.</p>' + table(fcs['actions'], [('seq_id','Contig'),('seq_len','Length (bp)'),('action','FCS action'),('div','Division'),('agg_cont_cov','FCS foreign-division alignment coverage (%)'),('top_tax_name','Top taxon label')]) + '<p><strong>No read fraction, sequencing depth or read-mapping breadth is available for this case.</strong> FCS alignment coverage and percentage of assembly bases are different measurements. Significance bins and likely sources remain student decisions. The original, retained and excluded FASTAs form an exact identifier partition, with sequence identity verified ignoring case. Cleaning converted lowercase sequence to uppercase, so soft-masking case was not preserved.</p><p>The original log records October 14, 2026 (timezone unspecified), database build January 24, 2023, and about 29,799 seconds (8.28 hours) processing. Job 102266 requested 40 GB and two CPUs; this is an allocation request, not measured peak memory or a general resource recommendation. No fresh container run was performed during this local integration.</p><p class="source">Evidence: <a href="fcs/decontamination/GCA_051997085.1.36331.fcs_gx_report.txt">original action report</a>; <a href="reports/fcs_analysis.md">case interpretation and provenance</a>; <a href="tables/fcs_detections.tsv">assembly detection table</a>; <a href="docs/15_fcs_linux.md">portable Linux instructions</a>; <a href="metadata/analysis_datasets.tsv">all datasets</a>. NCBI linkage: <a href="https://www.ncbi.nlm.nih.gov/bioproject/816194">BioProject assembly table</a>. The seven embedded figures above belong to the original DNA/RNA branches; no BlobToolKit plot was supplied for this additional genome.</p>')
    section('limits', 'Interpretation, reproducibility and unfinished work', '<ul><li>Noise, trace, consequential and biological bins remain the student’s decisions; source categories are not inferred automatically.</li><li>Human, fungal and other screening labels have not all undergone independent mapping validation.</li><li>FCS-GX completed for the additional G. irregulare genome only; no completed FCS report is retained for the original DNA/RNA assembly branches.</li><li>No DIAMOND viral-protein analysis, CheckV completeness result or independently validated RNA virus is reported.</li><li>No spike-in detection-limit experiment was performed.</li><li>The repository excludes raw reads and large regenerable intermediates. Compressed final assemblies, BlobDirs, tables, figures, software definitions and original logs are retained.</li><li>Historical completion markers describe the original HPC execution; removed intermediates and annotated source mean those markers must not be treated as current restart guarantees.</li><li>Archived original validation reports are distinguished from the fresh offline checks performed during repository curation.</li></ul><p>Open this HTML directly in a browser: all seven figures are embedded, with no remote fonts, styles or scripts. Linked TSV/log files require the repository; the narrative and images remain usable when this HTML alone is copied.</p>')
    section('files', 'Evidence and reproduction guide', '<div class="link-grid">' + ''.join(f'<a href="{path}">{title}</a>' for path,title in [('README.md','Detailed project README'),('QUICKSTART.md','Quickstart'),('docs/10_methods.md','Methods'),('docs/14_repository_guide.md','Repository and restoration guide'),('reports/one_page_writeup.md','One-page evidence writeup'),('reports/final_decisions.docx','Word final-decision worksheet'),('reports/analysis_summary.md','What ran, findings and meaning'),('reports/interpretation_guide.md','Metric and significance guide'),('reports/repository_validation.md','Current verification'),('tables/detections.tsv','Primary detection table'),('metadata/repository_cleanup.tsv','Cleanup inventory'),('metadata/retained_assemblies.json','Assembly checksums'),('provenance/README.md','Historical provenance')]) + '</div>')
    nav = ''.join(f'<a href="#{id}">{title}</a>' for id,title in [('overview','Overview'),('samples','Samples & QC'),('workflow','Workflow'),('screening','Screening'),('mapping','Mapping evidence'),('specificity','Specificity review'),('bracken','Bracken'),('assemblies','Assemblies'),('blobplots','Blobplots'),('figures','Other figures'),('history','Execution history'),('fcs','FCS-GX case'),('limits','Limitations'),('files','Files & methods')])
    css = '''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f4f5ef;color:#243b36;font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}a{color:#176451;text-underline-offset:3px}aside{position:fixed;width:220px;inset:0 auto 0 0;padding:32px 20px;background:#193f36;color:#fff;overflow:auto}aside strong{font-size:20px;line-height:1.2;display:block;margin-bottom:28px}nav a{display:block;padding:7px 10px;color:#dcece5;text-decoration:none;border-radius:5px;font-size:14px}nav a:hover{background:#2b594c}main{margin-left:220px;max-width:1500px;padding:46px 5vw 80px}header{border-bottom:2px solid #abc4b6;padding-bottom:30px}header .eyebrow,.section-label{font-size:12px;text-transform:uppercase;letter-spacing:.16em;color:#527467;font-weight:700}h1{font:600 clamp(30px,4vw,52px)/1.12 Georgia,serif;max-width:900px;margin:16px 0}h2{font:600 29px/1.25 Georgia,serif;margin:7px 0 20px}h3{font-size:19px;line-height:1.4}p{max-width:1000px}.lead{font-size:19px}.chips{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}.chips span{padding:6px 13px;background:#e2ebe1;border-radius:24px;font-size:13px}section{padding:40px 0 16px;border-bottom:1px solid #d7dfd4;scroll-margin-top:20px}.callout{background:#e6eee3;border-left:4px solid #39785a;padding:20px 24px;margin:22px 0}.table-wrap{overflow-x:auto;background:#fff;border:1px solid #d6dfd4;border-radius:8px;margin:22px 0;max-height:650px}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.45}th{text-align:left;background:#e8eee5;position:sticky;top:0;z-index:1;white-space:nowrap}th,td{padding:11px 14px;border-bottom:1px solid #e7eae2;vertical-align:top}tbody tr:nth-child(even){background:#f8faf5}td:first-child{font-weight:600}.source,figcaption{font-size:13px;color:#52665c;overflow-wrap:anywhere}figure{margin:26px 0;background:white;border:1px solid #d6dfd4;border-radius:10px;padding:22px}figure img{display:block;width:100%;height:auto;max-width:1100px;margin:auto}figcaption{padding-top:14px}.flow{max-width:800px;margin:24px auto;text-align:center}.flow div{padding:16px;background:#fff;border:1px solid #b9cdbb;border-radius:8px;font-weight:650}.flow b{font-size:24px;color:#53816a}.flow small{font-weight:400}.branch-grid,.link-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}.branch-grid>div{padding:8px 22px;background:#e9eee5;border-radius:8px}.link-grid a{background:#fff;padding:14px;border:1px solid #d6dfd4;border-radius:6px}.search-label{display:block;font-size:14px}input{padding:10px 14px;border:1px solid #9cb7a5;border-radius:6px;width:min(450px,100%);margin-left:12px;font:inherit}footer{margin-top:40px;color:#62746a;font-size:13px}@media(max-width:850px){aside{position:static;width:auto;padding:20px}aside strong{margin:0}nav{display:flex;overflow:auto;margin-top:10px}nav a{white-space:nowrap}main{margin:0;padding:25px 18px}.branch-grid,.link-grid{grid-template-columns:1fr}figure{padding:10px}input{margin-left:0;display:block}}@media print{aside,.search-label{display:none}main{margin:0;padding:0}.table-wrap{max-height:none;overflow:visible}section{break-before:auto}figure{break-inside:avoid}body{background:white}}'''
    script = "document.getElementById('filter').addEventListener('input',function(){const q=this.value.toLowerCase();document.querySelectorAll('table.searchable tbody tr').forEach(r=>{r.hidden=!r.textContent.toLowerCase().includes(q)})});"
    document = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Evidence-based oomycete contamination screening, de novo assemblies, and embedded BlobToolKit companion plots"><title>Oomycete contamination analysis — results and execution history</title><style>' + css + '</style></head><body><aside><strong>Oomycete<br>contamination analysis</strong><nav>' + nav + '</nav></aside><main><header><div class="eyebrow">HPC results · curated 20 October 2026</div><h1>From taxonomic hits<br>to defensible evidence.</h1><p>DNA WGS and RNA-seq screening, reference validation, de novo assemblies and BlobToolKit.</p><div class="chips"><span>2 independent readsets</span><span>100,000-pair screening</span><span>3 assembly visualisations</span><span>Original measurements preserved</span></div></header>' + ''.join(sections) + '<footer>Generated from retained repository evidence using scripts/build_report.py. No new biological analysis was run during report generation. Scientific significance and source assignments remain user decisions.</footer></main><script>' + script + '</script></body></html>'
    (ROOT / 'index.html').write_text(document)
    summary = dict(data, history=history, detection_rows=len(detections), embedded_figures=7, fcs_completed=True, virus_discovery_completed=False)
    (ROOT / 'reports/results_summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print('Wrote index.html, reports/results_summary.json and derived TSV summaries.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build()


if __name__ == '__main__':
    main()
