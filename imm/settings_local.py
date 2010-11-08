DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'imm'             # Or path to database file if using sqlite3.
DATABASE_USER = 'imm'             # Not used with sqlite3.
DATABASE_PASSWORD = 'imm123'         # Not used with sqlite3.
DATABASE_HOST = 'cmcf-sqldb.cs.clsi.ca'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# LDAP settings to use the LDAP Authentication backend
LDAP_DEBUG = True
LDAP_SERVER_URI = 'ldap://cmcf-ldap.cs.clsi.ca'
LDAP_SEARCHDN = 'dc=cmcf,dc=cls'
LDAP_SEARCH_FILTER = 'uid=%s'
LDAP_UPDATE_FIELDS = True
LDAP_FULL_NAME = 'cn'
LDAP_BINDDN = 'ou=people,dc=cmcf,dc=cls'
LDAP_BIND_ATTRIBUTE = 'uid'

USER_API_HOST = 'cmcf.lightsource.ca:443'
