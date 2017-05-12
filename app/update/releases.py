import subprocess


def _call_script(name, postprocess=None, **kwargs):
    def func(*args):
        cmd = 'bin/update/{}.sh'.format(name)
        has_default = 'default' in kwargs
        proc = subprocess.run(
            [cmd] + list(args),
            stdout=subprocess.PIPE,
            encoding='utf-8',
            check=not has_default)
        if has_default and proc.returncode != 0:
            value = kwargs['default']
        else:
            value = proc.stdout
            if postprocess is not None:
                value = postprocess(value)
        return value
    return func

current_version = _call_script('current-version', lambda v: v.strip(), default=None)
list_versions = _call_script('list-versions', lambda v: v.split())
update_to_latest = _call_script('update-latest')
revert = _call_script('revert')
