#!/usr/bin/env python3
import argparse
import json
import sys
from urllib import error, request


def _fetch(url, payload=None, timeout=15):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = request.Request(url, data=data, headers=headers, method='POST' if data else 'GET')
    with request.urlopen(req, timeout=timeout) as response:
        return response.status, response.read().decode('utf-8')


def run(base_url):
    base = base_url.rstrip('/')
    failures = []

    status, body = _fetch(base + '/healthz')
    health = json.loads(body)
    if status != 200 or health.get('status') != 'ok':
        failures.append('health check did not return status ok')
    if not health.get('retrieval', {}).get('chunks'):
        failures.append('knowledge base has no chunks')

    status, body = _fetch(base + '/api/chat', {'message': 'I have a cold'})
    payload = json.loads(body)
    if status != 200:
        failures.append(f'chat returned HTTP {status}')
    general = payload.get('general') or {}
    if general.get('scope') != 'general_health':
        failures.append('cold message was not routed to general health')
    if (payload.get('insight') or {}).get('citations'):
        failures.append('cold message received period citations')
    if ((payload.get('remedy') or {}).get('citations')):
        failures.append('cold message received remedy citations')

    return failures


def main():
    parser = argparse.ArgumentParser(description='Check a running recHERsion deployment.')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--timeout', type=int, default=15)
    args = parser.parse_args()

    try:
        failures = run(args.base_url)
    except (OSError, error.URLError, ValueError, json.JSONDecodeError) as exc:
        print(f'FAIL: {exc}')
        return 1

    if failures:
        for failure in failures:
            print(f'FAIL: {failure}')
        return 1
    print('PASS: health, knowledge base and cold-message scope checks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
