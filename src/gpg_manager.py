import subprocess
import os
import shutil
import re
from typing import Tuple, Optional

class GPGManager:
    def __init__(self):
        self.gpg_executable = shutil.which("gpg")

    def is_gpg_installed(self) -> bool:
        return self.gpg_executable is not None

    def generate_gpg_key(self, name: str, email: str, passphrase: str) -> Tuple[bool, str, str, str]:
        """
        Generates a GPG key using batch mode.
        Returns: (Success, Message, KeyID, PublicKeyBlock)
        """
        if not self.is_gpg_installed():
            return False, "GPG is not installed or not found in PATH.", "", ""

        # Batch Config
        # Using RSA 4096, 0 expiry (never)
        batch_config = f"""
Key-Type: 1
Key-Length: 4096
Subkey-Type: 1
Subkey-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
Passphrase: {passphrase}
%commit
"""
        
        try:
            # Run GPG generation
            process = subprocess.run(
                ["gpg", "--batch", "--gen-key"],
                input=batch_config,
                text=True,
                capture_output=True,
                encoding='utf-8'  # Force UTF-8
            )

            if process.returncode != 0:
                return False, f"GPG Generation Failed:\n{process.stderr}", "", ""

            # Generation usually prints to stderr. We need to find the key ID.
            # Output example:
            # gpg: key 7385AF37FCF5E2D8 marked as ultimately trusted
            # gpg: revocation certificate stored as '...'
            
            output_log = process.stderr + process.stdout
            
            # Regex to find Key ID (16 or 40 char hex)
            # Look for "gpg: key XXXXXXXX marked as ultimately trusted" OR "key XXXXXXXX created"
            match = re.search(r"key\s+([0-9A-F]+)\s+marked as ultimately trusted", output_log, re.IGNORECASE)
            if not match:
                 match = re.search(r"key\s+([0-9A-F]+)\s+created", output_log, re.IGNORECASE)
                 
            if match:
                key_id = match.group(1)
                
                # Get Public Key
                pub_key_process = subprocess.run(
                    ["gpg", "--armor", "--export", key_id],
                    text=True,
                    capture_output=True,
                    encoding='utf-8'
                )
                
                if pub_key_process.returncode == 0:
                    pub_key = pub_key_process.stdout
                    return True, "Key generated successfully.", key_id, pub_key
                else:
                    return True, "Key generated but failed to export public key.", key_id, ""
            
            # Fallback: Try list keys matching the email if regex failed
            # This is risky if multiple keys exist, but helpful as fallback
            list_proc = subprocess.run(
                ["gpg", "--list-keys", "--keyid-format", "LONG", email],
                text=True, capture_output=True, encoding='utf-8'
            )
            # Parse output for 'pub   rsa4096/1234567890ABCDEF'
            match_list = re.search(r"pub\s+rsa\d+/([0-9A-F]+)", list_proc.stdout, re.IGNORECASE)
            if match_list:
                key_id = match_list.group(1)
                # Export
                pub_key_proc = subprocess.run(["gpg", "--armor", "--export", key_id], text=True, capture_output=True, encoding='utf-8')
                return True, "Key generated successfully (Found via list).", key_id, pub_key_proc.stdout
            
            return False, f"Key generated but finding Key ID failed. Log:\n{output_log}", "", ""

        except Exception as e:
            return False, f"Error executing GPG: {str(e)}", "", ""
