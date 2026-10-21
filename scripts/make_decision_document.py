#!/usr/bin/env python3
"""Create a compact three-dataset Word assessment with explicitly provisional judgments.

Uses only the Python standard library and retained measurement tables. The user
requested inclusion of the discussed judgments; primary detection tables remain unchanged.
"""
import argparse
import csv
import json
from html import escape
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]


def paragraph(text, bold=False, size=19, after=70, color='263645', fill=None, accent=None, keep=False):
    """Create a readable paragraph; semantic headings stay with their following evidence."""
    props = f'<w:spacing w:after="{after}" w:line="225" w:lineRule="auto"/>'
    if keep:
        props += '<w:keepNext/>'
    if fill:
        props += f'<w:shd w:val="clear" w:fill="{fill}"/>'
    if accent:
        props += f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="{accent}"/></w:pBdr>'
    return f'<w:p><w:pPr>{props}</w:pPr><w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>{"<w:b/>" if bold else ""}<w:color w:val="{color}"/><w:sz w:val="{size}"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def assessment_table(dna, rna, fcs):
    """Make a compact, accessible summary with text labels as well as colour."""
    rows = [
        ['CASE', 'PROVISIONAL ASSESSMENT', 'KEY MEASUREMENT'],
        ['DNA WGS', 'Noise: species assignment', f"{dna['supporting_reads']} reads | {float(dna['read_fraction_percent']):.4f}% of reads"],
        ['RNA-seq', 'Noise / unresolved assignments', f"{rna['supporting_reads']} reads | {float(rna['read_fraction_percent']):.4f}% of reads"],
        ['FCS genome', 'Consequential for curation', f"{fcs['excluded_sequences']} contigs | {fcs['excluded_bases']:,} bp excluded"],
    ]
    widths = [1500, 3900, 4968]
    table = '<w:tbl><w:tblPr><w:tblW w:w="10368" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="65" w:type="dxa"/><w:left w:w="110" w:type="dxa"/><w:bottom w:w="65" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'
    table += ''.join(f'<w:gridCol w:w="{width}"/>' for width in widths) + '</w:tblGrid>'
    for index, row in enumerate(rows):
        fill = '17384A' if index == 0 else 'FFF1DB' if index == 3 else 'EDF4F6' if index == 1 else 'F5F8FA'
        table += '<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if index == 0 else '') + '</w:trPr>'
        for width, value in zip(widths, row):
            table += f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:shd w:fill="{fill}"/><w:vAlign w:val="center"/></w:tcPr>'
            table += paragraph(value, bold=(index == 0), size=17, after=0, color='FFFFFF' if index == 0 else '263645') + '</w:tc>'
        table += '</w:tr>'
    return table + '</w:tbl>'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    with (ROOT / 'tables/detections.tsv').open() as handle:
        rows = [row for row in csv.DictReader(handle, delimiter='\t') if row['mapping_mode'] == 'competitive']
    lookup = {(row['assay'], row['reference_id']): row for row in rows}
    dna = lookup[('DNA', 'Pseudomonas_CIP10')]
    rna = lookup[('RNA', 'Pseudomonas_CIP10')]
    fcs = json.loads((ROOT / 'reports/fcs_results.json').read_text())
    sections = [
        ('Oomycete contamination: final assessment', 'Three independent datasets; provisional judgments for student review. These assessments distinguish detection evidence from an unresolved contamination mechanism.'),
        ('1. DNA WGS: Globisporangium okanoganense CBS 315.81',
         f"SRR15309490. Pseudomonas CIP-10 competitive mapping retained {dna['supporting_reads']} reads ({float(dna['read_fraction_percent']):.4f}% of input reads), mean depth {float(dna['mean_depth']):.6f}x and breadth >=1x {float(dna['breadth_1x_percent']):.5f}%. All 143 alignments overlapped rRNA; representative reads also matched oomycete/eukaryotic records. Provisional bin: NOISE for the species assignment. Conserved-sequence cross-mapping is favoured; a bacterial source was not established. This does not prove that every supporting read is host-derived."),
        ('2. RNA-seq: Phytophthora hibernalis mycelium',
         f"SRR16206986. Pseudomonas competitive support was {rna['supporting_reads']} reads ({float(rna['read_fraction_percent']):.4f}%), depth {float(rna['mean_depth']):.6f}x and breadth {float(rna['breadth_1x_percent']):.5f}%. Of these, 126 overlap rRNA, one tRNA and one sucD; both mates of the sucD pair matched Phytophthora transcripts. Provisional bin: NOISE for Pseudomonas species identification. Miltoncostaea remains noise/unresolved: 11 reads cover only 130 bp with 7–11 mismatches per 90 bp. Conserved-sequence misassignment is more plausible than demonstrated microbial associates."),
        ('3. FCS-GX public genome: Globisporangium irregulare strain 13-30',
         f"GCA_051997085.1; PRJNA816194; SAMN26664723. Selected because the user reports an NCBI contamination flag; exact wording was not independently verified. Supplied completed HPC FCS-GX v0.5.0 output recommends EXCLUDE for {fcs['excluded_sequences']} complete fungal-labelled contigs: {fcs['excluded_bases']:,} bp ({fcs['excluded_assembly_percent']:.6f}% of assembly bases). Six have top label Cladosporium colombiae; two Melanodothis sp. Provisional bin: CONSEQUENTIAL for assembly curation, because retaining foreign contigs could distort annotation/comparative analysis; an actual downstream effect was not measured. Source: fungal sample/culture carryover suspected, mechanism unresolved. Species labels are provisional. No associated SRA run was verified; read fraction, depth and read-mapping breadth are unavailable."),
        ('Why alternative sources are not favoured',
         'A real associate/cobiont remains possible for the fungal contigs, but presence alone does not establish an association. Integration lacks host–fungal junction evidence. Reagent contamination lacks blanks/batch controls; bleed-through lacks multiplex/index evidence; library chimera lacks a validated chimeric junction. Human screening labels were not independently validated, and no laboratory provenance establishes a lab organism. Database error was not demonstrated: shared conserved sequence can produce ambiguous assignments without erroneous records.'),
        ('Scope and evidence',
         'The two readsets used 100,000 cleaned pairs each (200,000 input reads); depth/breadth include uncovered reference positions. Other selected reference negatives do not exclude all strains. Broader human/fungal screening labels and blobplot colours remain hypotheses. FCS assembly-base percentage is not read fraction; exclusion does not prove the retained genome is contamination-free. No independently validated RNA virus or spike-in detection limit is reported. Evidence: tables/detections.tsv; tables/fcs_actions.tsv; reports/fcs_analysis.md; reports/pseudomonas_specificity_review.md; original HPC logs.'),
    ]
    body = paragraph('CONTAMINATION SCREENING  /  EVIDENCE & JUDGMENT', True, 17, 60, color='237C82', keep=True)
    body += paragraph('Three datasets. One evidence-led assessment.', True, 38, 80, color='17384A', keep=True)
    body += paragraph(sections[0][1], size=19, after=110, color='566675', keep=True)
    body += assessment_table(dna, rna, fcs)
    body += paragraph('READ EVIDENCE ≠ ASSEMBLY FRACTION  •  Source mechanisms remain provisional', True, 16, 95, color='566675')
    for index, (heading, text) in enumerate(sections[1:], 1):
        accent = 'B87922' if index == 3 else '237C82'
        body += paragraph(heading, True, 21, 65, color='17384A', accent=accent, keep=True)
        body += paragraph(text, size=19, after=100)
    body += paragraph('STUDENT REVIEW / REVISIONS  __________________________________________________', size=16, after=0, color='566675')
    markdown = '# ' + sections[0][0] + '\n\n' + sections[0][1] + '\n\n'
    markdown += '\n\n'.join('## ' + heading + '\n\n' + text for heading, text in sections[1:])
    (ROOT / 'reports/final_decisions.md').write_text(markdown + '\n')
    section = '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="620" w:right="936" w:bottom="620" w:left="936" w:header="300" w:footer="300"/></w:sectPr>'
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + body + section + '</w:body></w:document>'
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'
    target = ROOT / 'reports/final_decisions.docx'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml', content_types)
        archive.writestr('_rels/.rels', relationships)
        archive.writestr('word/document.xml', document)
    print('Created:', target)


if __name__ == '__main__':
    main()
