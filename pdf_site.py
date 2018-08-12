#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf_site.py

Generates an index of PDF files, with JPG thumbnails of each one.

Usage:
    pdf_site.py [--max=<num> --log=<level>]

Options:
    --max=<num>     Maximum number of PDFs to include in the index.
                    [default: 30]
    --log=<level>   Logging level. [default: info]
"""

from datetime import datetime
import json
import logging
from pathlib import Path

import boto3
from docopt import docopt
import jinja2


TOP = Path(__file__).parent
WEBROOT = TOP.joinpath('html')
ASSETS = WEBROOT.joinpath('assets')
TEMPLATE = TOP.joinpath('index_template.html')

logging.basicConfig(
    format='%(asctime)s  %(levelname)-10s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)


try:
    with open('pdf-manifest.json') as f:
        manifest = json.load(f)
except FileNotFoundError:
    manifest = dict()


def list_files():
    log.debug('Listing directory {}'.format(ASSETS))
    files = [p.name for p in ASSETS.iterdir()
             if p.suffix in ('.jpg', '.pdf')]
    log.debug('list_files() found {} files'.format(len(files)))
    return files


def get_bucket():
    return boto3.resource('s3').Bucket('pdf.peoples-press.com')


def s3_objects(bucket):
    s3_objects = [o for o in bucket.objects.iterator()]
    log.debug('s3_objects() found {} keys'.format(len(s3_objects)))
    return s3_objects


def new_to_download(bucket, objects):
    log.debug('Downloading {} files from S3 bucket {} …'.format(
        len(objects), bucket.name))
    for o in objects:
        key = o.key
        bucket.download_file(key, str(ASSETS.joinpath(key)))
        log.debug('Downloaded: ' + key)
        manifest[o.key] = o.last_modified.isoformat()
        log.debug('Added to manifest: ' + key)


def date_from_base_names(base_names):
    for bn in base_names:
        year, month, day = (int(s) for s in bn.split('_')[1:])
        yield datetime(year, month, day)


def main(max_pdfs):
    log.info('Writing new PDF index')
    current_files = set(list_files())
    s3_bucket = get_bucket()
    s3_files = s3_objects(s3_bucket)

    to_download = [
        o for o in s3_files
        if ((o.key not in manifest) or
            (o.last_modified.isoformat() > manifest[o.key]))
        ]


    if not to_download:
        log.debug('No additional files to download')
    else:
        new_to_download(s3_bucket, to_download)
        with open('pdf-manifest.json', 'w') as f:
            json.dump(manifest, f, sort_keys=True, indent=2)
            log.debug('Wrote manifest to file')

    # Call list_files again in case anything was downloaded
    base_names = {s[:-4] for s in list_files()}
    pairs = zip(base_names, date_from_base_names(base_names))

    # Sort pairs by date and limit by MAX_PDFS
    log.debug('Limiting PDF index to {} files'.format(max_pdfs))
    selected_pairs = sorted(pairs, key=lambda t: t[1], reverse=True)[:max_pdfs]

    with open(str(WEBROOT.joinpath('index.html')), 'w') as f:
        rendered = jinja2.Template(TEMPLATE.read_text()).render(
            name_date_pairs=selected_pairs)
        f.write(rendered)
        log.info('Finished writing new PDF index')


if __name__ == '__main__':
    args = docopt(__doc__)

    log.setLevel(getattr(logging, args['--log'].upper()))
    log.debug('Called from the command line')
    log.debug('Arguments:\n{}'.format(args))

    max_pdfs = int(args['--max'])
    main(max_pdfs)
