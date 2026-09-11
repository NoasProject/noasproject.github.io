import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_poker_config import CONFIG_DIR, allows, load_config, validate, validate_file


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config((CONFIG_DIR/'v2/config.json').read_text())

    def test_existing_configs(self):
        validate_file(CONFIG_DIR/'config.json')
        validate_file(CONFIG_DIR/'v2/config.json')

    def test_invalid_fields(self):
        for key, value in [
            ('allowed_versions', []), ('allowed_versions', ['.*']),
            ('allowed_versions', [r'^2\.0\.(a+)+$']),
            ('allowed_versions', [r'^2\.0\.0$', r'^2\.0\.0$']),
            ('force_update', 'true'), ('store_url', 'https://apps.apple.com/app/idXXXXXXXX'),
            ('message', {'ja': 'test'}), ('message', {'ja': '', 'en': 'test'}),
            ('message_key', 'unknownMessage'),
        ]:
            with self.subTest(key=key, value=value):
                config = copy.deepcopy(self.config)
                config['ios'][key] = value
                with self.assertRaises(ValueError): validate(config, v2=True)

    def test_missing_and_typo_keys(self):
        for key in set(self.config['ios']):
            config = copy.deepcopy(self.config)
            del config['ios'][key]
            with self.assertRaises(ValueError): validate(config, v2=True)
        self.config['ios']['force_udpate'] = True
        with self.assertRaises(ValueError): validate(self.config, v2=True)

    def test_supported_pause_methods(self):
        for product in ['', None]:
            self.config['ios']['products'][0]['store_product_id'] = product
            validate(self.config, v2=True)
        self.config['ios']['products'][0]['purchase_enabled'] = False
        validate(self.config, v2=True)

    def test_offline_access_must_be_valid(self):
        for value in [
            {'access_hours': 0, 'reminder_hours': [24, 10, 3]},
            {'access_hours': 50, 'reminder_hours': [10, 24, 3]},
            {'access_hours': 50, 'reminder_hours': [24, 24, 3]},
            {'access_hours': 50, 'reminder_hours': [50, 10, 3]},
        ]:
            config = copy.deepcopy(self.config)
            config['ios']['offline_access'] = value
            with self.assertRaises(ValueError): validate(config, v2=True)

    def test_product_ids_and_keys_must_be_valid(self):
        product = self.config['ios']['products'][0]
        for key, value in [
            ('id', 'invalid product id'),
            ('store_product_id', 'invalid product id'),
            ('accepted_product_ids', []),
            ('purchase_enabled', 'false'),
            ('promotions', None),
        ]:
            with self.subTest(key=key, value=value):
                config = copy.deepcopy(self.config)
                config['ios']['products'][0][key] = value
                with self.assertRaises(ValueError): validate(config, v2=True)
        product['accepted_product_ids'] = ['old.product.id']
        with self.assertRaises(ValueError): validate(self.config, v2=True)

    def test_promotion_must_be_valid_and_common_to_both_platforms(self):
        promotion = {
            'percent_off': 30,
            'starts_at': 1788238800,
            'ends_at': 1790780400,
        }
        self.config['ios']['products'][0]['promotions'] = [promotion]
        self.config['android']['products'][0]['promotions'] = [copy.deepcopy(promotion)]
        validate(self.config, v2=True)
        for invalid in [
            {'percent_off': 0, 'starts_at': 1788238800, 'ends_at': 1790780400},
            {'percent_off': 100, 'starts_at': 1788238800, 'ends_at': 1790780400},
            {'percent_off': 30, 'starts_at': 1790780400, 'ends_at': 1788238800},
            {'percent_off': 30, 'starts_at': '1788238800', 'ends_at': 1790780400},
        ]:
            config = copy.deepcopy(self.config)
            config['ios']['products'][0]['promotions'] = [invalid]
            config['android']['products'][0]['promotions'] = [copy.deepcopy(invalid)]
            with self.assertRaises(ValueError): validate(config, v2=True)
        overlapping = copy.deepcopy(promotion)
        overlapping['starts_at'] = promotion['ends_at'] - 1
        overlapping['ends_at'] = promotion['ends_at'] + 100
        for os in ('ios', 'android'):
            self.config[os]['products'][0]['promotions'].append(
                copy.deepcopy(overlapping)
            )
        with self.assertRaises(ValueError): validate(self.config, v2=True)
        self.config = load_config((CONFIG_DIR/'v2/config.json').read_text())
        self.config['ios']['products'][0]['promotions'] = [promotion]
        self.config['android']['products'][0]['promotions'] = [copy.deepcopy(promotion)]
        self.config['android']['products'][0]['promotions'][0]['percent_off'] = 20
        with self.assertRaises(ValueError): validate(self.config, v2=True)

    def test_version_matching(self):
        self.config['ios']['allowed_versions'] = [r'^2\.0\.0$', r'^2\.1\.[0-9]+$']
        validate(self.config, v2=True)
        self.assertTrue(allows(self.config, 'ios', '2.0.0'))
        self.assertTrue(allows(self.config, 'ios', '2.1.42'))
        self.assertFalse(allows(self.config, 'ios', '2.0.1'))
        self.assertFalse(allows(self.config, 'ios', '12.0.0'))

    def test_duplicate_json_keys(self):
        with self.assertRaises(ValueError): load_config('{"ios":{},"ios":{}}')


if __name__ == '__main__': unittest.main()
