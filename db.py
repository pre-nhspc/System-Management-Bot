from tinydb import TinyDB, Query
from tinydb.table import Document
from typing import Any, Dict, List, Union

import config


def _get_user_schema() -> Dict[str, Any]:
    """Return a template for user object"""
    return {
        'discord_id': None,  # Discord User ID
        'username': None,  # Username for Workstation/CMS/etc.
        'is_sysadm': False,
        'ssh_keys': [],  # List of ssh keys
    }


class DB(object):
    """Wrapper for our TinyDB backend"""

    def __init__(self, db_path):
        self.db = TinyDB(db_path)
        self.Users = self.db.table('users')
        self.Q = Query()

    def get_user_by_discord_id(self, discord_id: int) -> Union[Document, None]:
        """Retrieve user object by Discord ID, or None if not found."""
        return self.Users.get(self.Q.discord_id == discord_id)

    def update_user(self, user: Union[Dict[str, Any], Document]) -> bool:
        """Update (part of the) user. Return true if success

        The user object should at least contains the key `discord_id`.
        """
        assert 'discord_id' in user
        res = self.Users.update(user, self.Q.discord_id == user['discord_id'])
        assert len(res) <= 1
        return len(res) == 1

    def get_all_sysadm_user(self) -> List[Document]:
        """Get the list of all system-admin user object."""
        return self.Users.search(self.Q.is_sysadm == True)

    def create_user(self, user_data: Dict[str, Any]) -> bool:
        """Create a user. Return true if success."""
        user = _get_user_schema()
        user.update(user_data)
        if user.get('discord_id', None) is None or user.get('username', None) is None:
            return False  # Missing/Empty fields
        if self.get_user_by_discord_id(user['discord_id']) is not None:
            return False  # User already exists
        self.Users.insert(user)
        return True

    def delete_user(self, user: Union[Dict[str, Any], Document]) -> bool:
        """Delete a user. Return true if success

        The user object should at least contains the key `discord_id`.
        """
        assert 'discord_id' in user
        res = self.Users.remove(self.Q.discord_id == user['discord_id'])
        assert len(res) <= 1
        return len(res) == 1


# Shared DB Connection
db = DB(config.DB_PATH)
