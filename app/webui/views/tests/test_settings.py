import json
import os.path
import unittest

import flask_testing
import pyfakefs.fake_filesystem_unittest

import webui


class SettingsTest(pyfakefs.fake_filesystem_unittest.TestCase, flask_testing.TestCase):

    def create_app(self):
        webui.app.config['TESTING'] = True
        webui.app.config['PROFILE_DIRECTORY'] = 'profiles'
        return webui.app

    def setUp(self):
        self.setUpPyfakefs()
        self.copyRealFile(os.path.join(os.path.dirname(__file__), 'profile.xlsx'), 'profiles/profile1.xlsx')

    def test_profile_delete(self):
        self.assertTrue(os.path.exists('profiles/profile1.xlsx'))
        self.client.post('/settings/profile/delete', data={'temperatureprofile': 'profile1'})
        self.assertFalse(os.path.exists('profiles/profile1.xlsx'))


if __name__ == '__main__':
    unittest.main()
