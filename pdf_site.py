#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import re

import boto3
import jinja2


MAX_PDFS = 31

assets_dir = Path('assets')
asset_regex = re.compile(r'MS_(20\d{2})_(0[1-9]|1[0-2])_([0-2]\d|3[0-2]).pdf')

def list_pdfs():
    return [p.name[:-4] for p in assets_dir.iterdir()
            if asset_regex.match(p.name)]


def render_jinja(template, name_date_pairs):
    return jinja2.Template(template).render(
        name_date_pairs=name_date_pairs)


def date_from_base_names(base_names):
    for bn in base_names:
        year, month, day = (int(s) for s in bn.split('_')[1:])
        yield datetime(year, month, day)

base_names = list_pdfs()
pairs = zip(base_names, date_from_base_names(base_names))

# Sort pairs by date and limit by MAX_PDFS
selected_pairs = sorted(pairs, key=lambda t: t[1], reverse=True)[:MAX_PDFS]

html_template = Path('index_template.html').read_text()
print(render_jinja(html_template, selected_pairs))
