#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import re

import boto3
import jinja2


MAX_PDFS = 31

assets_dir = Path('assets')
asset_regex = re.compile(r'MS_(20\d{2})_(0[1-9]|1[0-2])_([0-2]\d|3[0-2]).pdf')

#webroot = Path('/srv/www/pdfs.morningstaronline.co.uk/html/')
#template = Path('/srv/www/pdfs.morningstaronline.co.uk/index_template.html')

webroot = Path('/Users/admin/projects/rjw-ms-pdf-site/html/')
template = Path('/Users/admin/projects/rjw-ms-pdf-site/index_template.html')


def list_files():
    return [p.name for p in assets_dir.iterdir()
            if asset_regex.match(p.name)]


def get_bucket():
    s = boto3.resource('s3')
    return s.Bucket('pdf.peoples-press.com')


def s3_object_names(bucket):
    return [o.key for o in bucket.objects.iterator()]

def new_to_download(bucket, names):
    for key in names:
        print(key)
        bucket.download_file(key, str(webroot.joinpath('assets', key)))
        print('Downloaded ' + key)


def render_jinja(template, name_date_pairs):
    return jinja2.Template(template).render(
        name_date_pairs=name_date_pairs)


def date_from_base_names(base_names):
    for bn in base_names:
        year, month, day = (int(s) for s in bn.split('_')[1:])
        yield datetime(year, month, day)


if __name__ == '__main__':
    current_files = set(list_files())
    s3_bucket = get_bucket()
    s3_files = s3_object_names(s3_bucket)
    to_download = [f for f in s3_files if f not in current_files]
    new_to_download(s3_bucket, to_download)

    base_names = {s[:-4] for s in list_files()}
    pairs = zip(base_names, date_from_base_names(base_names))

    # Sort pairs by date and limit by MAX_PDFS
    selected_pairs = sorted(pairs, key=lambda t: t[1], reverse=True)[:MAX_PDFS]

    html_template = Path('index_template.html').read_text()
    with open(webroot.joinpath('index.html'), 'w') as f:
        f.write(render_jinja(html_template, selected_pairs))
