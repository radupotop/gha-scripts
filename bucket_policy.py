import json
import sys
from copy import deepcopy
from itertools import chain
from pathlib import Path

import boto3
import requests

from skel import S3_POLICY_SKEL

OUTPUT_DIR = 'aws'
S3 = boto3.client('s3')


ADDR_LIST = (
    'https://www.cloudflare.com/ips-v6',
    'https://www.cloudflare.com/ips-v4'
)

DOMAINS = (
    'wooptoo.com',
    'static.wooptoo.com'
)


def _process_addrs(addr):
    resp = requests.get(addr)
    resp.raise_for_status()
    lines_resp = resp.text.strip().split('\n')
    return sorted(lines_resp)


def read_ips():
    list_ips = [_process_addrs(addr) for addr in ADDR_LIST]
    return list(chain(*list_ips))


def read_skel():
    return deepcopy(S3_POLICY_SKEL)


def process_domain(domain):
    skel = read_skel()
    skel['Statement'][0]['Resource'] = skel['Statement'][0]['Resource'].replace('DOMAIN', domain)
    skel['Statement'][0]['Condition']['IpAddress']['aws:SourceIp'] = read_ips()
    return skel


def write_to_file(domain, result):
    if Path(OUTPUT_DIR).is_dir():
        filepath = Path(OUTPUT_DIR) / f'{domain}-s3-policy.json'
        filepath.write_text(result)
        print(f'Wrote to file: {filepath}\n')
    else:
        print('Could not locate output directory')
        sys.exit(1)


def process_all(write_file=False):
    for domain in DOMAINS:
        result = json.dumps(process_domain(domain), indent=4)
        print(f'Processing {domain}')
        print(result)

        if write_file:
            write_to_file(domain, result)
        else:
            policy_ret = S3.put_bucket_policy(Bucket=domain, Policy=result)
            print(f'AmazonS3 response {policy_ret}')


if __name__ == '__main__':
    process_all(len(sys.argv) > 1)
