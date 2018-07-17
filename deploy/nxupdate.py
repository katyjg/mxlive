#!/usr/bin/env python
#
# This script updates the NoMachine user access list, usually /usr/NX/etc/users.db
# it should be copied to the nomachine server, updated to match the cerverand a cron entry should be created to run the script as often as needed
#

SERVER_URL = "https://cmcf.lightsource.ca" # Address of MxLIVE Server
SSL_VERIFY = False   # Set to False to allow self-signed certificates


# --------------    DO NOT EDIT BELOW HERE   ------------------ #

import requests
import socket
import subprocess
import msgpack


NX_TEMPLATE = "# --------- Allowed NX Users on %s ---------\n# This file is generated automatically, do not edit. Use MxLIVE!\n\n%s\n"


def update_userlist():
    url = "%s/api/v2/accesslist/" % SERVER_URL
    cmd = "/usr/NX/bin/nxserver --history"
    outp = subprocess.check_output(cmd.split())
    info = [o.split() for o in outp.split('\n')[3:] if o]

    connections = [{
                       'project': conn[1],
                       'name': conn[3],
                       'date': "{} {}".format(conn[4], conn[5]),
                       'status': conn[6]
                    } for conn in info]

    data = msgpack.dumps(connections)
    if not SSL_VERIFY:
        r = requests.post(url, data=data, verify=SSL_VERIFY)
    else:
        r = requests.post(url, data=data)

    if r.status_code == requests.codes.ok:
        users = r.json()
        hostname = socket.gethostname()
        users_text = "\n".join(users)
        return NX_TEMPLATE % (hostname, users_text)



    #TODO: Terminate unauthorized connections now.
    return ""


if __name__ == "__main__":
    data = update_userlist()
    if data:
        with open('/usr/NX/etc/users.db', 'w') as fobj:
            fobj.write(data)




