import os
from collections import namedtuple
from glob import iglob

import pandas as pd
from flask import current_app

Profile = namedtuple('Profile', 'profile_id, name, trajectory')


def load_profiles():
    profile_directory = current_app.config['PROFILE_DIRECTORY']
    profiles = dict()
    for filename in iglob(os.path.join(profile_directory, '*.xlsx')):
        profileid = os.path.splitext(os.path.basename(filename))[0]
        data = pd.read_excel(filename)
        time = data.iloc[:, 0].values.tolist() * 60
        temperature = data.iloc[:, 1].values.tolist()
        trajectory = list(zip(time, temperature))
        profiles[profileid] = Profile(profileid, profileid, trajectory)
    return profiles


def delete_profile(profileid):
    profile_directory = current_app.config['PROFILE_DIRECTORY']
    # TODO: this could potentially delete ANY file, not only the ones in 'temperature-profiles' directory
    os.remove(os.path.join(profile_directory, '{}.xlsx'.format(profileid)))
