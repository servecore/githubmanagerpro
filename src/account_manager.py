import json
import os
import uuid
from typing import List, Dict, Optional

ACCOUNTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'accounts.json')

class AccountManager:
    def __init__(self, storage_file: str = ACCOUNTS_FILE):
        self.storage_file = storage_file
        self.accounts: List[Dict] = self._load_accounts()

    def _load_accounts(self) -> List[Dict]:
        if not os.path.exists(self.storage_file):
            return []
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_accounts(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.accounts, f, indent=4)

    def add_account(self, alias: str, username: str, email: str, ssh_key_path: str, gpg_key_id: str = None) -> Dict:
        """Adds a new account and saves it."""
        new_account = {
            "id": str(uuid.uuid4()),
            "alias": alias,
            "username": username,
            "email": email,
            "ssh_key_path": ssh_key_path,
            "gpg_key_id": gpg_key_id
        }
        self.accounts.append(new_account)
        self._save_accounts()
        return new_account

    def update_account(self, account_id: str, alias: str, username: str, email: str, ssh_key_path: str, gpg_key_id: str = None) -> Optional[Dict]:
        """Updates an existing account."""
        for acc in self.accounts:
            if acc["id"] == account_id:
                acc["alias"] = alias
                acc["username"] = username
                acc["email"] = email
                acc["ssh_key_path"] = ssh_key_path
                acc["gpg_key_id"] = gpg_key_id
                self._save_accounts()
                return acc
        return None

    def delete_account(self, account_id: str) -> bool:
        """Deletes an account by ID."""
        initial_count = len(self.accounts)
        self.accounts = [acc for acc in self.accounts if acc["id"] != account_id]
        if len(self.accounts) < initial_count:
            self._save_accounts()
            return True
        return False

    def get_accounts(self) -> List[Dict]:
        """Returns list of all accounts."""
        return self.accounts

    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        for acc in self.accounts:
            if acc["id"] == account_id:
                return acc
        return None
