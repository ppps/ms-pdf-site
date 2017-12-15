#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf_site.py

Generates an index of PDF files, with JPG thumbnails of each one.

Usage:
    pdf_site.py [--max=<num>]

Options:
    --max=<num>     Maximum number of PDFs to include in the index.
                    [default: 30]
"""

from datetime import datetime
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
log.setLevel(logging.INFO)


def list_files():
    log.debug('Listing directory {}'.format(ASSETS))
    files = [p.name for p in ASSETS.iterdir()
             if p.suffix in ('.jpg', '.pdf')]
    log.debug('list_files() found {} files'.format(len(files)))
    return files


def get_bucket():
    return boto3.resource('s3').Bucket('pdf.peoples-press.com')


def s3_object_names(bucket):
    s3_keys = [o.key for o in bucket.objects.iterator()]
    log.debug('s3_object_names() found {} keys'.format(len(s3_keys)))
    return s3_keys


def new_to_download(bucket, names):
    log.debug('Downloading {} files from S3 bucket {} …'.format(
        len(names), bucket.name))
    for key in names:
        bucket.download_file(key, str(ASSETS.joinpath(key)))
        log.debug('Downloaded: ' + key)


def date_from_base_names(base_names):
    for bn in base_names:
        year, month, day = (int(s) for s in bn.split('_')[1:])
        yield datetime(year, month, day)


def main(max_pdfs):
    log.info('Writing new PDF index')
    current_files = set(list_files())
    s3_bucket = get_bucket()
    s3_files = s3_object_names(s3_bucket)
    to_download = [f for f in s3_files if f not in current_files]
    if not to_download:
        log.debug('No additional files to download')
    else:
        new_to_download(s3_bucket, to_download)

    base_names = {s[:-4] for s in current_files}
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
    log.debug('Called from the command line')
    args = docopt(__doc__)
    log.debug('Arguments: {}'.format(args))
    max_pdfs = int(args['--max'])
    main(max_pdfs)
