import re
import subprocess


def _git_get_head():
    proc = subprocess.run('git rev-parse HEAD', stdout=subprocess.PIPE, encoding='utf-8', check=True)
    return proc.stdout


def _git_list_tags():
    proc = subprocess.run(
        'git for-each-ref --sort=taggerdate --format "%(object) %(tag)" refs/tags',
        stdout=subprocess.PIPE, encoding='utf-8', check=True)
    return proc.stdout


def current_release():
    try:
        head = _git_get_head().strip()
        for release_hash, release_name in list_releases():
            if release_hash == head:
                return release_name
    except subprocess.CalledProcessError:
        pass


def list_releases():
    regex = re.compile('^(\w+)\s+(.+?)$')
    releases = []
    try:
        for line in _git_list_tags().split('\n'):
            m = regex.match(line)
            if m is not None:
                releases.append((m.group(1), m.group(2)))
        return releases
    except subprocess.CalledProcessError:
        return []
