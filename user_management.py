import ldap
import ldap.modlist
import os
import pwd
import subprocess
from typing import List

import config


class LDAPConn(object):
    """Representing connection to a LDAP instance with simple get/update/delete interface"""

    def __init__(self):
        self.ld = ldap.initialize(config.LDAP_URI)
        self.ld.simple_bind_s(who=config.LDAP_ROOTUSER,
                              cred=config.LDAP_ROOTUSER_PASSWD)

    def delete_entry(self, dn: str) -> bool:
        """Delete entry on LDAP, return True if success"""
        try:
            self.ld.delete_s(dn)
        except ldap.NO_SUCH_OBJECT:
            return False
        return True

    def get_entry(self, dn: str) -> dict:
        """Retrieve LDAP entry by dn

        Return: The entry, should be a dict. Or None if not found
        """
        result_list = self.ld.search_s(dn, ldap.SCOPE_SUBTREE)

        if len(result_list) == 0:
            return None

        assert len(result_list) == 1
        _, entry = result_list[0]

        return entry

    def update_entry(self, dn: str, new_entry: dict) -> bool:
        """Update entry on LDAP, return True if success"""
        old_entry = self.get_entry(dn)
        if old_entry is None:
            return False

        modlist = ldap.modlist.modifyModlist(old_entry, new_entry)
        self.ld.modify_s(dn, modlist)
        return True


def _uid_to_ldap_dn(user_id: str) -> str:
    return f"uid={user_id},ou=people,{config.LDAP_BASE}"


def _gid_to_ldap_dn(group_id: str) -> str:
    return f"cn={group_id},ou=groups,{config.LDAP_BASE}"


def unix_user_exists(user_id: str) -> bool:
    """Return whether the given user_id exists on this unix system (including LDAP)"""
    try:
        pwd.getpwnam(user_id)
    except KeyError:
        return False
    return True


def create_ldap_user(user_id: str) -> bool:
    """Create new user on LDAP

    Note: This is using external shell script

    Retrun: True if successful, else False
    """
    # TODO: Rewrite the logic in python
    r = subprocess.run(["bash", "./adduser.sh", user_id])
    return r.returncode == 0


def delete_ldap_user(user_id: str) -> bool:
    """Remove user from LDAP, return True if success"""
    conn = LDAPConn()
    success = conn.delete_entry(_uid_to_ldap_dn(user_id))
    if not success:
        return False
    if os.path.isdir(f'/home/{user_id}'):
        r = subprocess.run(['sudo', 'rm', '-rf', f'/home/{user_id}'])
        assert r.returncode == 0
    return True


def update_user_sshkey_list(user_id: str, keys: List[str]) -> bool:
    """Update user's list of SSH Public Key, return True if success"""
    conn = LDAPConn()
    byte_keys = [key.encode('utf-8') for key in keys]
    user_dn = _uid_to_ldap_dn(user_id)
    user_entry = conn.get_entry(user_dn)
    if user_entry is None:
        return False
    user_entry['sshPublicKey'] = byte_keys
    conn.update_entry(user_dn, user_entry)
    return True


def update_group_member_list(group_id: str, member_uids: List[str]) -> bool:
    """Update a specific group's member list, return True if success"""
    conn = LDAPConn()
    byte_member_uids = [uid.encode('utf-8') for uid in member_uids]
    group_dn = _gid_to_ldap_dn(group_id)
    group_entry = conn.get_entry(group_dn)
    if group_entry is None:
        return False
    group_entry['memberUid'] = byte_member_uids
    conn.update_entry(group_dn, group_entry)
    return True


def update_user_login_shell(user_id: str, shell: str) -> bool:
    """Update user's login shell, return True if success"""
    conn = LDAPConn()
    byte_shell = shell.encode('utf-8')
    user_dn = _uid_to_ldap_dn(user_id)
    user_entry = conn.get_entry(user_dn)
    if user_entry is None:
        return False
    user_entry['loginShell'] = [byte_shell]
    conn.update_entry(user_dn, user_entry)
    return True
