import os.path
import unittest

import pyfakefs.fake_filesystem_unittest

import webui
from webui.models.profiles import load_profiles, load_profile, delete_profile


class ProfilesTest(pyfakefs.fake_filesystem_unittest.TestCase):

    def setUp(self):
        self.setUpPyfakefs()
        profile_filename = os.path.join(os.path.dirname(__file__), 'profile.xlsx')
        self.copyRealFile(profile_filename, 'profiles/profile1.xlsx')
        self.copyRealFile(profile_filename, 'profiles/profile2.xlsx')

        self.trajectory = [
            (0.0, 20.0, 'Phase 1'),
            (30.0, 30.0, 'Phase 2'),
            (300.0, 50.0, 'Phase 3'),
            (900.0, 60.0, 'Phase 4'),
            (1200.0, 60.0, 'Phase 5'),
            (1800.0, 50.0, 'Phase 6'),
            (3600.0, 20.0, 'Phase 7'),
        ]

        webui.app.config['TESTING'] = True
        webui.app.config['PROFILE_DIRECTORY'] = 'profiles'

    def test_load_profiles(self):
        with webui.app.app_context():
            profiles = load_profiles()
        self.assertEqual(list(profiles.keys()), ['profile1', 'profile2'])
        self.assertEqual(list(profiles.values()), [self.trajectory, self.trajectory])

    def test_load_profile(self):
        with webui.app.app_context():
            trajectory = load_profile('profile1')
        self.assertEqual(trajectory, self.trajectory)

    def test_load_non_existent_profile(self):
        with self.assertRaises(FileNotFoundError):
            with webui.app.app_context():
                load_profile('profile3')

    def test_delete_profile(self):
        self.assertTrue(os.path.exists('profiles/profile1.xlsx'))
        with webui.app.app_context():
            delete_profile('profile1')
        self.assertFalse(os.path.exists('profiles/profile1.xlsx'))
        self.assertTrue(os.path.exists('profiles/profile2.xlsx'))

    def test_delete_non_existent_profile(self):
        try:
            with webui.app.app_context():
                delete_profile('profile2')
        except FileNotFoundError:
            self.fail('FileNotFoundError should not be raised')


if __name__ == '__main__':
    unittest.main()
