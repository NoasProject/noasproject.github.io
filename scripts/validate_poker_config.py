#!/usr/bin/env python3
"""Validate BlindScale configs before publishing. Standard library only."""
import argparse
import json
import re
from datetime import date
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parents[1] / 'products/poker-blind-tournament/config'
PRODUCT_ID_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')
MESSAGE_KEYS = {'updateUnsupportedVersionMessage', 'updateAvailableMessage'}
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
        optional = set()
        if v2:
            required = {
                'allowed_versions', 'force_update', 'store_url', 'message_key',
                'offline_access_hours', 'connection_reminder_hours',
                'study_pro_product_id', 'study_pro_entitlement_product_ids',
                'study_pro_purchase_enabled',
            }
            optional = {'study_pro_promotion'}
        if (not isinstance(settings, dict) or not required <= set(settings) or
                not set(settings) <= required | optional):
            raise ValueError(
                f'{os}: missing or unknown keys '
                f'(required {sorted(required)}, optional {sorted(optional)})'
            )
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
        if v2:
            if settings['message_key'] not in MESSAGE_KEYS:
                raise ValueError(f'{os}.message_key: unknown bundled translation key')
            offline_hours = settings['offline_access_hours']
            reminder_hours = settings['connection_reminder_hours']
            if type(offline_hours) is not int or not 1 <= offline_hours <= 720:
                raise ValueError(f'{os}.offline_access_hours: integer from 1 through 720 required')
            if (not isinstance(reminder_hours, list) or len(reminder_hours) > 10 or
                    any(type(value) is not int for value in reminder_hours) or
                    len(set(reminder_hours)) != len(reminder_hours) or
                    any(value < 1 or value >= offline_hours for value in reminder_hours) or
                    any(left <= right for left, right in zip(reminder_hours, reminder_hours[1:]))):
                raise ValueError(
                    f'{os}.connection_reminder_hours: up to 10 unique descending integers '
                    'between 1 and offline_access_hours - 1 required'
                )
            if type(settings['study_pro_purchase_enabled']) is not bool:
                raise ValueError(f'{os}.study_pro_purchase_enabled: boolean required')
            product_id = settings['study_pro_product_id']
            if product_id not in ('', None) and (
                    not isinstance(product_id, str) or not PRODUCT_ID_PATTERN.fullmatch(product_id)):
                raise ValueError(f'{os}.study_pro_product_id: invalid product ID')
            if settings['study_pro_purchase_enabled'] and not product_id:
                raise ValueError(f'{os}.study_pro_product_id: required while purchases are enabled')
            entitlement_ids = settings['study_pro_entitlement_product_ids']
            if (not isinstance(entitlement_ids, list) or not entitlement_ids or
                    any(not isinstance(value, str) or not PRODUCT_ID_PATTERN.fullmatch(value)
                        for value in entitlement_ids) or
                    len(set(entitlement_ids)) != len(entitlement_ids)):
                raise ValueError(f'{os}.study_pro_entitlement_product_ids: unique valid product IDs required')
            if product_id and product_id not in entitlement_ids:
                raise ValueError(f'{os}.study_pro_entitlement_product_ids: must include active product ID')
            promotion = settings.get('study_pro_promotion')
            if promotion is not None:
                if not isinstance(promotion, dict) or set(promotion) != {'percent_off', 'ends_on'}:
                    raise ValueError(f'{os}.study_pro_promotion: percent_off and ends_on required')
                percent_off = promotion['percent_off']
                ends_on = promotion['ends_on']
                if type(percent_off) is not int or not 1 <= percent_off <= 99:
                    raise ValueError(f'{os}.study_pro_promotion.percent_off: integer from 1 through 99 required')
                if not isinstance(ends_on, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', ends_on):
                    raise ValueError(f'{os}.study_pro_promotion.ends_on: YYYY-MM-DD required')
                try:
                    date.fromisoformat(ends_on)
                except ValueError as error:
                    raise ValueError(f'{os}.study_pro_promotion.ends_on: invalid date') from error
        else:
            messages = settings['message']
            if not isinstance(messages, dict) or not {'ja', 'en'} <= set(messages):
                raise ValueError(f'{os}.message: ja and en required')
            if any(not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
                   for k, v in messages.items()):
                raise ValueError(f'{os}.message: nonempty language keys and texts required')


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
