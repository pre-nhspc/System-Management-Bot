#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail -o errtrace

source "./config.py"
UIDNUMBER_BASE=3000

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <username>"
    exit 1
fi

username="$1"

all_user_info=$(ldapsearch -x cn=* -b "ou=people,${LDAP_BASE}" -H "${LDAP_URI}" -D "${LDAP_ROOTUSER}" -w "${LDAP_ROOTUSER_PASSWD}")

if (echo "${all_user_info}" | grep "^uid: ${username}$" > /dev/null); then
    echo "The user '${username}' already exists!!!"
    exit 1
fi

used_uid_number=( $(echo "${all_user_info}" | { grep "^uidNumber:" || true; } | sed 's/uidNumber: //g') )
uid=${UIDNUMBER_BASE}

while [[ " ${used_uid_number[@]} " =~ " ${uid} " ]]; do
    uid=$((uid+1))
done

ldapadd -x -H "${LDAP_URI}" -D "${LDAP_ROOTUSER}" -w "${LDAP_ROOTUSER_PASSWD}" > /dev/null <<EOF
dn: uid=${username},ou=people,${LDAP_BASE}
objectClass: top
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
objectClass: ldapPublicKey
cn: ${username}
uid: ${username}
uidNumber: ${uid}
gidNumber: 8000
homeDirectory: /home/${username}
loginShell: /bin/bash
surName: NHSPC
givenName: Staff
EOF

echo "Added user ${username} with uidNumber ${uid}"
