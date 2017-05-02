import os.path
import unittest

import pyfakefs.fake_filesystem_unittest

import webui
from webui.models.profiles import load_profile, delete_profile


class ProfilesTest(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self):
        self.setUpPyfakefs()
        self.copyRealFile('profile.xlsx', 'profiles/profile1.xlsx')

        webui.app.config['TESTING'] = True
        webui.app.config['PROFILE_DIRECTORY'] = 'profiles'

    def test_load_profile(self):
        with webui.app.app_context():
            name, trajectory = load_profile('profile1')
        self.assertEqual(name, 'profile1')
        self.assertEqual(
            trajectory,
            [
                (0.0, 20.0),
                (30.0, 30.0),
                (300.0, 50.0),
                (900.0, 60.0),
                (1200.0, 60.0),
                (1800.0, 50.0),
                (3600.0, 20.0),
            ])

    def test_load_non_existent_profile(self):
        with self.assertRaises(FileNotFoundError):
            with webui.app.app_context():
                load_profile('profile2')

    def test_delete_profile(self):
        self.assertTrue(os.path.exists('profiles/profile1.xlsx'))
        with webui.app.app_context():
            delete_profile('profile1')
        self.assertFalse(os.path.exists('profiles/profile1.xlsx'))

    def test_delete_non_existent_profile(self):
        try:
            with webui.app.app_context():
                delete_profile('profile2')
        except FileNotFoundError:
            self.fail('FileNotFoundError should not be raised')


if __name__ == '__main__':
    unittest.main()
