import unittest
from subprocess import CalledProcessError
from unittest.mock import patch

from webui.models.update import current_release, list_releases


@patch('webui.models.update._git_list_tags')
@patch('webui.models.update._git_get_head')
class UpdateTests(unittest.TestCase):

    def test_list_releases(self, git_get_head, git_list_tags):
        git_list_tags.return_value = '''
f94efd05884413f11d1c1729353d6811d6e35e97 Tag1
746d6272b61ba1149b4a5cf368021fea7313157d Tag-2
'''
        releases = list_releases()
        self.assertEqual(
            releases,
            [
                ('f94efd05884413f11d1c1729353d6811d6e35e97', 'Tag1'),
                ('746d6272b61ba1149b4a5cf368021fea7313157d', 'Tag-2')
            ]
        )

    def test_list_releases_error(self, git_get_head, git_list_tags):
        git_list_tags.side_effect = CalledProcessError(1, '')
        releases = list_releases()
        self.assertEqual(releases, [])

    def test_current_release(self, git_get_head, git_list_tags):
        git_get_head.return_value = ' f94efd05884413f11d1c1729353d6811d6e35e97 \n'
        git_list_tags.return_value = '''
f94efd05884413f11d1c1729353d6811d6e35e97 Tag1
746d6272b61ba1149b4a5cf368021fea7313157d Tag-2
'''
        release = current_release()
        self.assertEqual(release, 'Tag1')

    def test_current_release_unknown(self, git_get_head, git_list_tags):
        git_get_head.return_value = '17c351f2d6eef76e18720cac9c2a54c494b32baf'
        git_list_tags.return_value = '''
f94efd05884413f11d1c1729353d6811d6e35e97 Tag1
746d6272b61ba1149b4a5cf368021fea7313157d Tag-2
'''
        release = current_release()
        self.assertEqual(release, None)

    def test_current_release_error(self, git_get_head, git_list_tags):
        git_get_head.side_effect = CalledProcessError(1, '')
        releases = current_release()
        self.assertEqual(releases, None)


if __name__ == '__main__':
    unittest.main()
