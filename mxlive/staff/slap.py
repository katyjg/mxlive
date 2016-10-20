from django.conf import settings

from ldap import modlist, cidict
import ldap
from ldap.controls import SimplePagedResultsControl
import StringIO
import ldif
import random
import string
from distutils.version import StrictVersion

# Check if we're using the Python "ldap" 2.4 or greater API
LDAP24API = StrictVersion(ldap.__version__) >= StrictVersion('2.4')

PAGESIZE = 1000
ldap.set_option(ldap.OPT_DEBUG_LEVEL, 0)
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, 0)
ldap.set_option(ldap.OPT_REFERRALS, 0)

BASE_DN = getattr(settings, 'LDAP_BASE_DN', 'dc=example,dc=com')
SERVER_URI = getattr(settings, 'AUTH_LDAP_SERVER_URI', 'ldaps://ldap.example.com')
ADMIN_CN = getattr(settings, 'LDAP_ADMIN_CN', 'cn=Directory Manager')
ADMIN_SECRET = getattr(settings, 'LDAP_ADMIN_SECRET', 'Admin123')
USER_TABLE = getattr(settings, 'LDAP_USER_TABLE', 'ou=People')
USER_ROOT = getattr(settings, 'LDAP_USER_ROOT', '/home')
GROUP_TABLE = getattr(settings, 'LDAP_GROUP_TABLE', 'ou=Groups')

USER_ATTRIBUTES = ['cn', 'uid', 'uidNumber', 'gidNumber', 'homeDirectory', 'loginShell', 'description', 'gecos']


def create_controls(pagesize):
    """Create an LDAP control with a page size of "pagesize"."""
    # Initialize the LDAP controls for paging. Note that we pass ''
    # for the cookie because on first iteration, it starts out empty.
    if LDAP24API:
        return SimplePagedResultsControl(True, size=pagesize, cookie='')
    else:
        return SimplePagedResultsControl(ldap.LDAP_CONTROL_PAGE_OID, True,
                                         (pagesize, ''))


def get_pctrls(serverctrls):
    """Lookup an LDAP paged control object from the returned controls."""
    # Look through the returned controls and find the page controls.
    # This will also have our returned cookie which we need to make
    # the next search request.
    if LDAP24API:
        return [c for c in serverctrls
                if c.controlType == SimplePagedResultsControl.controlType]
    else:
        return [c for c in serverctrls
                if c.controlType == ldap.LDAP_CONTROL_PAGE_OID]


def set_cookie(lc_object, pctrls, pagesize):
    """Push latest cookie back into the page control."""
    if LDAP24API:
        cookie = pctrls[0].cookie
        lc_object.cookie = cookie
        return cookie
    else:
        est, cookie = pctrls[0].controlValue
        lc_object.controlValue = (pagesize, cookie)
        return cookie


def res2ldif(result):
    dn, attrs = result
    out = StringIO.StringIO()
    ldif_out = ldif.LDIFWriter(out)
    ldif_out.unparse(dn, attrs)
    return out.getvalue()


def res2dict(result):
    dn, attrs = result
    out = cidict.cidict(attrs)
    return {k: v[0] for k, v in out.items()}


def get_username(name, existing):
    unroot = (u'%s' % name).replace('-', '').replace(' ', '').strip().lower()
    choices = [unroot] + ['{}{}'.format(unroot, i) for i in range(1, 20)]
    cands = sorted((set(choices) - set(existing)))
    return cands[0]


def add_user(info, connection=None):
    import sys
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI, trace_level=0, trace_file=sys.stderr)
        BIND_DN = ADMIN_CN
        con.bind_s(BIND_DN, ADMIN_SECRET, ldap.AUTH_SIMPLE)

    # Generate username here
    users = {user['uid']: int(user['uidNumber']) for user in dir_users(con)}

    if 'username' not in info:
        info['username'] = get_username(info['last_name'], users.keys())

    if 'password' not in info:
        info['password'] = nice_pass()

    uidNumber = gidNumber = max(users.values()) + 1

    # ldap has unicode issues, encode everything to 'utf-8'
    user_dn = u'uid={},{},{}'.format(info['username'], USER_TABLE, BASE_DN)
    user_record = {
        'cn': info['username'].encode('utf-8'),
        'uid': info['username'].encode('utf-8'),
        'gecos': '{} {}'.format(info['first_name'], info['last_name']),
        'homeDirectory': '{}/{}'.format(USER_ROOT, info['username']),
        'loginShell': '/bin/bash',
        'uidNumber': '{}'.format(uidNumber),
        'gidNumber': '{}'.format(gidNumber),
        'objectclass': ['top', 'account', 'posixAccount', 'shadowAccount'],
        'userPassword': info['password'],
    }

    group_dn = u'cn={},{},{}'.format(info['username'], GROUP_TABLE, BASE_DN)
    group_record = {
        'cn': info['username'],
        'gidNumber': gidNumber,
    }

    try:
        res = con.add_s(group_dn, modlist.addModlist(group_record))
        res = con.add_s(user_dn, modlist.addModlist(user_record))
        success = True
    except ldap.LDAPError as e:
        print e
        success = False

    if not connection:
        con.unbind_s()

    return info


def del_user(username, connection=None):
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI)
        con.bind_s(ADMIN_CN, ADMIN_SECRET, ldap.AUTH_SIMPLE)

    user_dn = u'uid=%s,%s,%s' % (username, USER_TABLE, BASE_DN)
    group_dn = u'cn=%s,ou=Groups,%s' % (username, BASE_DN)
    try:
        res = con.delete_s(user_dn)
        res = con.delete_s(group_dn)
        success = True
    except ldap.LDAPError as e:
        print e
        success = False

    if not connection:
        con.unbind_s()
    return success


def update_user(old_info, new_info, connection=None):
    # Only run if changes exist
    old_entry = {p for p in old_info.items()}
    new_entry = {p for p in new_info.items()}
    changed_values = dict(new_entry - old_entry)

    if changed_values:
        if connection:
            con = connection
        else:
            con = ldap.initialize(SERVER_URI)
            con.simple_bind_s(ADMIN_CN, ADMIN_SECRET)

        dn = u'uid=%s,%s,%s' % (old_info['username'], USER_TABLE, BASE_DN)
        record = [(ldap.MOD_REPLACE, k, v) for k, v in changed_values.items()]
        try:
            con.modify_s(dn, record)
            success = True
        except ldap.LDAPError as e:
            print e
            success = False

        if not connection:
            con.unbind_s()
    else:
        # no changes
        success = True
    return success


def change_password(username, old_password, new_password):
    con = ldap.initialize(SERVER_URI)
    bind_dn = u'uid=%s,%s,%s' % (username, USER_TABLE, BASE_DN)
    try:
        con.bind_s(bind_dn, old_password, ldap.AUTH_SIMPLE)
        success = reset_password(username, new_password)
    except ldap.LDAPError as e:
        success = e.message['desc']

    con.unbind_s()
    return success


def reset_password(username, new_password, connection=None):
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI)
        con.bind_s(ADMIN_CN, ADMIN_SECRET, ldap.AUTH_SIMPLE)

    dn = u'uid=%s,%s,%s' % (username, USER_TABLE, BASE_DN)
    info = [(ldap.MOD_REPLACE, 'userPassword', new_password)]

    try:
        con.modify_s(dn, info)
        success = True
    except ldap.LDAPError as e:
        print e
        success = False

    if not connection:
        con.unbind_s()
    return success


def dir_users(connection=None):
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI)
        con.simple_bind_s(ADMIN_CN, ADMIN_SECRET)
    con.protocol_version = 3
    lc = create_controls(PAGESIZE)

    filt = '(objectclass=posixAccount)'
    attrs = ['uid', 'uidNumber']
    search_dn = '{},{}'.format(USER_TABLE, BASE_DN)
    results = []

    while True:
        msgid = con.search_ext(search_dn, ldap.SCOPE_SUBTREE, filt, attrs, serverctrls=[lc])
        rtype, rdata, rmsgid, serverctrls = con.result3(msgid)
        results.extend(rdata)
        pctrls = get_pctrls(serverctrls)
        if not pctrls:
            break
        cookie = set_cookie(lc, pctrls, PAGESIZE)
        if not cookie:
            break

    if not connection:
        con.unbind_s()
    return [res2dict(r) for r in results]


def fetch_users(connection=None):
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI)
        con.simple_bind_s(ADMIN_CN, ADMIN_SECRET)

    con.protocol_version = 3
    lc = create_controls(PAGESIZE)

    filt = '(objectclass=posixAccount)'
    attrs = USER_ATTRIBUTES
    search_dn = '%s,%s' % (USER_TABLE, BASE_DN)
    results = []

    while True:
        msgid = con.search_ext(search_dn, ldap.SCOPE_SUBTREE, filt, attrs, serverctrls=[lc])
        rtype, rdata, rmsgid, serverctrls = con.result3(msgid)
        results.extend(rdata)
        pctrls = get_pctrls(serverctrls)
        if not pctrls:
            break
        cookie = set_cookie(lc, pctrls, PAGESIZE)
        if not cookie:
            break

    if not connection:
        con.unbind_s()
    return '\n'.join([res2ldif(r) for r in results])


def fetch_user(username, connection=None):
    if connection:
        con = connection
    else:
        con = ldap.initialize(SERVER_URI)
        con.simple_bind_s(ADMIN_CN, ADMIN_SECRET)

    filt = '(objectclass=posixAccount)'
    attrs = USER_ATTRIBUTES
    search_dn = 'uid={},{},{}'.format(username, USER_TABLE, BASE_DN)
    results = con.search_s(search_dn, ldap.SCOPE_SUBTREE, filt, attrs)

    if not connection:
        con.unbind_s()
    return [res2dict(r) for r in results]


def nice_pass(alpha=6, numeric=3):
    """
    returns a human-readble password (say rol816din instead of
    a difficult to remember K8Yn9muL )
    """
    vowels = ['a', 'e', 'i', 'o', 'u']
    consonants = [a for a in string.ascii_lowercase if a not in vowels]
    digits = string.digits

    ####utility functions
    def a_part(slen):
        ret = ''
        for i in range(slen):
            if i % 2 == 0:
                randid = random.randint(0, 20)  # number of consonants
                ret += consonants[randid]
            else:
                randid = random.randint(0, 4)  # number of vowels
                ret += vowels[randid]
        ret = ''.join([random.choice([k, k, k, k.upper()]) for k in ret])
        return ret

    def n_part(slen):
        ret = ''
        for i in range(slen):
            randid = random.randint(0, 9)  # number of digits
            ret += digits[randid]
        return ret

    ####
    fpl = alpha / 2
    if alpha % 2:
        fpl = int(alpha / 2) + 1
    lpl = alpha - fpl

    start = a_part(fpl)
    mid = n_part(numeric)
    end = a_part(lpl)

    return "%s%s%s" % (start, mid, end)
