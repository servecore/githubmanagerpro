import json
import os
from typing import List, Dict, Optional

REPOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'repositories.json')

class RepositoryManager:
    def __init__(self, storage_file: str = REPOS_FILE):
        self.storage_file = storage_file
        self.repos: List[Dict] = self._load_repos()

    def _load_repos(self) -> List[Dict]:
        if not os.path.exists(self.storage_file):
            return []
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def _save_repos(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.repos, f, indent=4)

    def add_repo(self, path: str, alias: str, account_id: str) -> Dict:
        # Check if already exists
        for repo in self.repos:
            if repo["path"] == path:
                 repo["alias"] = alias
                 repo["account_id"] = account_id
                 self._save_repos()
                 return repo

        new_repo = {
            "path": path,
            "alias": alias,
            "account_id": account_id
        }
        self.repos.append(new_repo)
        self._save_repos()
        return new_repo

    def remove_repo(self, path: str):
        self.repos = [r for r in self.repos if r["path"] != path]
        self._save_repos()

    def get_repos(self) -> List[Dict]:
        return self.repos
