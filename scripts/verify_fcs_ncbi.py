#!/usr/bin/env python3
"""Retrieve exact NCBI assembly metadata and attempt BioSample-linked SRA discovery.

This performs metadata requests only; it never downloads sequencing data or
claims an SRA accession when a request fails. Cached raw responses are retained.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accession', default='GCA_051997085.1')
    parser.add_argument('--biosample', default='SAMN26664723')
    parser.add_argument('--output', default='metadata/fcs_ncbi')
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.mkdir(parents=True, exist_ok=True)
    def request(endpoint, parameters, name):
        destination = output / name
        if destination.exists():
            data = destination.read_bytes()
        else:
            url = BASE + endpoint + '?' + urlencode(parameters)
            print('QUERY', url, flush=True)
            with urlopen(url, timeout=60) as response:
                data = response.read()
            destination.write_bytes(data)
            time.sleep(0.4)
        return data
    status = {'accession':args.accession, 'biosample_query':args.biosample, 'assembly_verified':False, 'sra_verified':False}
    try:
        result = json.loads(request('esearch.fcgi', {'db':'assembly','term':args.accession+'[Assembly Accession]','retmode':'json'}, args.accession+'.search.json'))
        ids = result['esearchresult']['idlist']
        if len(ids) != 1:
            raise ValueError('Assembly accession did not resolve uniquely')
        summary = json.loads(request('esummary.fcgi', {'db':'assembly','id':ids[0],'retmode':'json'}, args.accession+'.summary.json'))['result'][ids[0]]
        if summary['assemblyaccession'] != args.accession:
            raise ValueError('NCBI returned another assembly version')
        status.update(assembly_verified=True, assembly_summary=summary)
    except Exception as error:
        status['assembly_lookup_error'] = str(error)
    try:
        result = json.loads(request('esearch.fcgi', {'db':'sra','term':args.biosample+'[BioSample]','retmode':'json','retmax':100}, args.biosample+'.sra_search.json'))
        ids = result['esearchresult']['idlist']
        if ids:
            raw = request('efetch.fcgi', {'db':'sra','id':','.join(ids),'rettype':'runinfo','retmode':'text'}, args.biosample+'.runinfo.csv')
            rows = list(csv.DictReader(io.StringIO(raw.decode())))
            exact = [row for row in rows if row.get('BioSample') == args.biosample and row.get('Run')]
            status.update(sra_verified=bool(exact), sra_runs=exact)
        else:
            status['sra_runs'] = []
            status['sra_note'] = 'No records returned for this query at lookup time; this is not proof of universal absence.'
    except Exception as error:
        status['sra_lookup_error'] = str(error)
    (output / 'verification_result.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(status, indent=2))
    return 0 if status['assembly_verified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
