#!/usr/bin/env python3
"""Validate BlindScale configs before publishing. Standard library only."""
import argparse
import json
import re
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[1] / 'products/poker-blind-tournament/config'
PRODUCT_ID = 'poker.tournament.blind.floor.study_pro'
STORE_URLS = {
    'ios': 'https://apps.apple.com/app/id6760666099',
    'android': 'https://play.google.com/store/apps/details?id=noas.poker.tournament.blind.floor',
}


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def load_config(text):
    return json.loads(text, object_pairs_hook=reject_duplicates)


def validate(config, *, v2):
    if not isinstance(config, dict) or set(config) != {'ios', 'android'}:
        raise ValueError('root must contain exactly ios and android')
    for os, settings in config.items():
        required = {'allowed_versions', 'force_update', 'store_url', 'message'}
        if v2:
            required |= {'study_pro_product_id', 'study_pro_purchase_enabled'}
        if not isinstance(settings, dict) or set(settings) != required:
            raise ValueError(f'{os}: missing or unknown keys (expected {sorted(required)})')
        versions = settings['allowed_versions']
        if not isinstance(versions, list) or not versions:
            raise ValueError(f'{os}.allowed_versions: nonempty array required')
        if any(not isinstance(value, str) for value in versions) or len(set(versions)) != len(versions):
            raise ValueError(f'{os}.allowed_versions: unique string patterns required')
        for pattern in versions:
            # A deliberate, safe subset shared by Dart/ECMAScript and Python.
            parts = pattern[1:-1].split(r'\.')
            if not pattern.startswith('^') or not pattern.endswith('$') or len(parts) != 3 or any(
                not (re.fullmatch(r'0|[1-9][0-9]*', part) or part == '[0-9]+') for part in parts
            ):
                raise ValueError(f'{os}.allowed_versions: unsupported pattern {pattern!r}; use ^2\\.0\\.0$ or ^2\\.0\\.[0-9]+$')
            re.compile(pattern)
        if type(settings['force_update']) is not bool:
            raise ValueError(f'{os}.force_update: boolean required')
        if settings['store_url'] != STORE_URLS[os]:
            raise ValueError(f'{os}.store_url: must be {STORE_URLS[os]}')
        messages = settings['message']
        if not isinstance(messages, dict) or not {'ja', 'en'} <= set(messages):
            raise ValueError(f'{os}.message: ja and en required')
        if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
               for k, v in messages.items()):
            raise ValueError(f'{os}.message: nonempty language keys and texts required')
        if v2:
            if type(settings['study_pro_purchase_enabled']) is not bool:
                raise ValueError(f'{os}.study_pro_purchase_enabled: boolean required')
            if settings['study_pro_product_id'] not in (PRODUCT_ID, '', None):
                raise ValueError(f'{os}.study_pro_product_id: expected registered ID, empty string, or null')


def allows(config, platform, version):
    if not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('app version must be major.minor.patch')
    return any(re.fullmatch(pattern, version) for pattern in config[platform]['allowed_versions'])


def validate_file(path):
    config = load_config(path.read_text(encoding='utf-8'))
    validate(config, v2=path.parent.name == 'v2')
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path)
    parser.add_argument('--version')
    parser.add_argument('--platform', choices=['ios', 'android'], default='ios')
    args = parser.parse_args()
    if args.version and not args.file:
        parser.error('--version requires --file')
    try:
        for path in [args.file] if args.file else [CONFIG_DIR/'config.json', CONFIG_DIR/'v2/config.json']:
            config = validate_file(path)
            if args.version and not allows(config, args.platform, args.version):
                raise ValueError(f'{args.platform}: version {args.version} is not allowed in {path}')
            print(f'Config validation passed: {path}')
    except (ValueError, OSError) as error:
        parser.exit(1, f'Config validation failed: {error}\n')


if __name__ == '__main__':
    main()
