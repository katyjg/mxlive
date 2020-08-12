#!/usr/bin/env python
#
# This script updates the NoMachine user access list, usually /usr/NX/etc/users.db
# it should be copied to the nomachine server, updated to match the cerverand a cron entry should be created to run the script as often as needed
#

SERVER_URL = "https://mxlive.lightsource.ca" # Address of MxLIVE Server
SSL_VERIFY = False   # Set to False to allow self-signed certificates
SSH_GROUP = 'mxlive'

# --------------    DO NOT EDIT BELOW HERE   ------------------ #

import requests
import socket
import subprocess
import msgpack

import warnings
warnings.filterwarnings("ignore")


def update_userlist():
    url = "%s/api/v2/accesslist/" % SERVER_URL

    # Get list of current and past connections
    cmd = "/usr/bin/last -Rw --time-format iso"
    outp = subprocess.check_output(cmd.split())
    info = [o.split() for o in outp.decode().split('\n') if o]

    connections = [{
        'project': conn[0],
        'name': '-'.join(conn[:3]),
        'date': 'still' in conn[3] and '{} {}'.format(
            conn[2].split('T')[0], conn[2].split('T')[1].split('-')[0]) or '{} {}'.format(
            conn[4].split('T')[0], conn[4].split('T')[1].split('-')[0]),
        'status': 'still' in conn[3] and 'Connected' or 'Finished'
    } for conn in info if 'pts' in conn[1] and 'root' not in conn]
    data = msgpack.dumps(connections)

    if not SSL_VERIFY:
        r = requests.post(url, data=data, verify=SSL_VERIFY)
    else:
        r = requests.post(url, data=data)

    if r.status_code == requests.codes.ok:
        authorized_users = r.json()

        for u in authorized_users:
            cmd = "usermod -a -G {} {}".format(SSH_GROUP, u)
            subprocess.check_call(cmd.split())

        # Get list of currently allowed users
        cmd = "groupmems -g {} -l".format(SSH_GROUP)
        outp = subprocess.check_output(cmd.split())
        current_users = [o.strip() for o in outp.decode().split()]

        to_remove = set(current_users) - set(authorized_users)
        for u in to_remove:
            cmd = "gpasswd -d {} {}".format(u, SSH_GROUP)
            subprocess.check_call(cmd.split())

    return ""


if __name__ == "__main__":
    data = update_userlist()
