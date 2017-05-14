import unittest
import os
import subprocess

from update.releases import list_versions, update_to_latest, current_version, revert


@unittest.skipUnless(
    'TRAVIS' in os.environ,
    'Run these tests only on travic-ci, because the current git repository will be changed'
)
class ReleasesTests(unittest.TestCase):

    def setUp(self):
        subprocess.run(os.path.join(os.path.dirname(__file__), 'create-test-repo.sh'), check=True)

    def tearDown(self):
        subprocess.run(os.path.join(os.path.dirname(__file__), 'cleanup-test-repo.sh'), check=True)

    def test_update(self):
        update_to_latest()
        self.assertEqual(current_version(), 'tmp-test-version-3')

        self.assertEqual(list_versions()[-3:], ['tmp-test-version-1', 'tmp-test-version-2', 'tmp-test-version-3'])

        revert('tmp-test-version-1')
        self.assertEqual(current_version(), 'tmp-test-version-1')

        self.assertEqual(list_versions()[-3:], ['tmp-test-version-1', 'tmp-test-version-2', 'tmp-test-version-3'])


if __name__ == '__main__':
    unittest.main()
