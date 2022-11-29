# Please copy this to config.py
# Note that adduser.sh is also going to source this file

LDAP_URI="ldaps://ldap.example.com/"
LDAP_BASE="dc=example,dc=com"
LDAP_ROOTUSER="cn=admin,dc=example,dc=com"
LDAP_ROOTUSER_PASSWD="thisisdefinitelynotthecorrectpassword"

DISCORD_TOKEN="7H15-15-AL50-D3f1N173ly-n07-7h3-C0RR3C7-70K3N"
DISCORD_CHANNEL_ID=123456789012345678 # Channel to listen to
SYSADM_ROLE_IDS=[876543210987654321] # List of role that should get the admin group

DB_PATH="./db.json"