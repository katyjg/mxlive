#!/usr/bin/env python
#
# This script updates the NoMachine user access list, usually /usr/NX/etc/users.db
# it should be copied to the nomachine server, updated to match the cerverand a cron entry should be created to run the script as often as needed
#

SERVER_URL = "https://opi2051-002.clsi.ca:9393" # Address of MxLIVE Server
SSL_VERIFY = True   # Set to False to allow self-signed certificates


# --------------    DO NOT EDIT BELOW HERE   ------------------ #

import requests
import socket

NX_TEMPLATE = "# --------- Allowed NX Users on {} ---------\n# This file is generated automatically, do not edit\n\n{}\n"


def fetch_userlist():
    url = "{}/api/accesslist/".format(SERVER_URL)
    if not SSL_VERIFY:
        r = requests.get(url, verify=SSL_VERIFY)
    else:
        r = requests.get(url)

    if r.status_code == requests.codes.ok:
        users = r.json()
        hostname = socket.gethostname()
        users_text = "\n".join(users)
        return NX_TEMPLATE.format(hostname, users_text)
    return ""

if __name__ == "__main__":
    data = fetch_userlist()
    if data:
        with open('/usr/NX/etc/users.db', 'w') as fobj:
            fobj.write(data)




