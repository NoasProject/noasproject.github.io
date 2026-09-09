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
            ('study_pro_product_id', 'wrong.id'), ('study_pro_purchase_enabled', 'false'),
        ]:
            with self.subTest(key=key, value=value):
                config = copy.deepcopy(self.config)
                config['ios'][key] = value
                with self.assertRaises(ValueError): validate(config, v2=True)

    def test_missing_and_typo_keys(self):
        for key in self.config['ios']:
            config = copy.deepcopy(self.config)
            del config['ios'][key]
            with self.assertRaises(ValueError): validate(config, v2=True)
        self.config['ios']['force_udpate'] = True
        with self.assertRaises(ValueError): validate(self.config, v2=True)

    def test_supported_pause_methods(self):
        for product in ['', None]:
            self.config['ios']['study_pro_product_id'] = product
            validate(self.config, v2=True)
        self.config['ios']['study_pro_purchase_enabled'] = False
        validate(self.config, v2=True)

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
