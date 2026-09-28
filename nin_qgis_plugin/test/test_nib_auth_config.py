# coding=utf-8
"""The NiB token is stored as a reusable EsriToken authentication configuration."""

import unittest

from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from qgis.core import QgsApplication, QgsAuthMethodConfig  # noqa: E402

from nin_qgis_plugin.project_setup import NIB_AUTHCFG_NAME, ensure_nib_auth_config  # noqa: E402


class TestNibAuthConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # utilities.get_qgis_app() points QGIS_AUTH_DB_DIR_PATH at a temp dir,
        # so this master password never touches the user's authentication db
        manager = QgsApplication.authManager()
        if not manager.masterPasswordIsSet():
            assert manager.setMasterPassword('nin-test-password', True)

    def _configs_named_like_plugin(self):
        manager = QgsApplication.authManager()
        return {
            config_id: config
            for config_id, config in manager.availableAuthMethodConfigs().items()
            if config.name() == NIB_AUTHCFG_NAME
        }

    def test_token_is_stored_once_and_updated_on_rerun(self):
        first_id, error = ensure_nib_auth_config('first-token-0123456789')
        self.assertIsNone(error)
        self.assertTrue(first_id)

        second_id, error = ensure_nib_auth_config('second-token-0123456789')
        self.assertIsNone(error)
        self.assertEqual(first_id, second_id, 'renewing the token must reuse the config')

        configs = self._configs_named_like_plugin()
        self.assertEqual(list(configs), [first_id])
        self.assertEqual(configs[first_id].method(), 'EsriToken')

        manager = QgsApplication.authManager()
        loaded = QgsAuthMethodConfig()
        self.assertTrue(manager.loadAuthenticationConfig(first_id, loaded, True))
        self.assertEqual(loaded.config('token'), 'second-token-0123456789')


if __name__ == '__main__':
    unittest.main()
