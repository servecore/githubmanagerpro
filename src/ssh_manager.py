import os
import subprocess
import shutil
from typing import Optional

class GitSwitcher:
    def __init__(self):
        self.ssh_config_path = os.path.expanduser("~/.ssh/config")
        self.ssh_dir = os.path.expanduser("~/.ssh")

    def generate_ssh_key(self, email: str, filename: str, output_dir: Optional[str] = None) -> tuple[bool, str, str]:
        """
        Generates an ed25519 SSH key.
        Returns: (Success, Message, PublicKeyContent)
        """
        try:
            # Determine directory
            target_dir = output_dir if output_dir else self.ssh_dir
            
            # Ensure directory exists
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            
            # Full path for the key
            key_path = os.path.join(target_dir, filename)
            pub_key_path = f"{key_path}.pub"
            
            if os.path.exists(key_path):
                return False, f"Key file already exists: {key_path}", ""

            # Run ssh-keygen
            # -t ed25519: key type
            # -C email: comment
            # -f key_path: output file
            # -N "": empty passphrase (for automation convenience, though less secure)
            cmd = [
                "ssh-keygen", "-t", "ed25519",
                "-C", email,
                "-f", key_path,
                "-N", ""
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Read public key
            with open(pub_key_path, 'r') as f:
                pub_key_content = f.read().strip()
                
            return True, f"Key generated at {key_path}", pub_key_content
            
        except subprocess.CalledProcessError as e:
            return False, f"ssh-keygen failed: {e.stderr.decode()}", ""
        except Exception as e:
            return False, f"Error generating key: {str(e)}", ""

    def set_global_git_user(self, name: str, email: str, gpg_key_id: str = None):
        """Sets the global git user.name, user.email, and GPG signing."""
        try:
            subprocess.run(["git", "config", "--global", "user.name", name], check=True)
            subprocess.run(["git", "config", "--global", "user.email", email], check=True)
            
            if gpg_key_id and gpg_key_id.strip():
                subprocess.run(["git", "config", "--global", "user.signingkey", gpg_key_id.strip()], check=True)
                subprocess.run(["git", "config", "--global", "commit.gpgsign", "true"], check=True)
            else:
                # Unset if not provided to avoid using wrong key
                subprocess.run(["git", "config", "--global", "--unset", "user.signingkey"], check=False)
                subprocess.run(["git", "config", "--global", "commit.gpgsign", "false"], check=False)
                
            return True, "Git global config updated."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to set git config: {e}"

    def set_local_git_user(self, repo_path: str, name: str, email: str, ssh_key_path: str):
        """
        Sets local git config for a repository.
        Also sets core.sshCommand to use specific key.
        """
        if not os.path.exists(os.path.join(repo_path, ".git")):
             return False, "Not a valid git repository (no .git folder)."

        try:
            # Fix path separators for Windows git bash compatibility if needed, 
            # often forward slashes work best in git config
            ssh_key_path_fixed = ssh_key_path.replace("\\", "/")
            
            # 1. User Identity
            subprocess.run(["git", "config", "--local", "user.name", name], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "--local", "user.email", email], cwd=repo_path, check=True)
            
            # 2. SSH Command Override
            # We use -F /dev/null to ignore global config and -i to specify key
            ssh_cmd = f"ssh -i \"{ssh_key_path_fixed}\" -o IdentitiesOnly=yes -F /dev/null"
            subprocess.run(["git", "config", "--local", "core.sshCommand", ssh_cmd], cwd=repo_path, check=True)
            
            return True, "Repository config updated successfully."
        except subprocess.CalledProcessError as e:
            return False, f"Failed to set local config: {e}"

    def get_current_global_user(self):
        try:
            name = subprocess.check_output(["git", "config", "--global", "user.name"], text=True).strip()
            email = subprocess.check_output(["git", "config", "--global", "user.email"], text=True).strip()
            return name, email
        except:
            return None, None

    def check_if_using_https(self) -> bool:
        """Checks if the user is likely using HTTPS credential helper."""
        try:
            # Check global credential helper
            helper = subprocess.check_output(["git", "config", "--global", "credential.helper"], text=True).strip()
            if helper:
                return True
        except:
            pass
        return False

    def get_current_ssh_identity(self) -> Optional[str]:
        """Tries to parse ~/.ssh/config to find the IdentityFile for github.com"""
        if not os.path.exists(self.ssh_config_path):
            return None
            
        try:
            with open(self.ssh_config_path, 'r') as f:
                lines = f.readlines()
                
            in_github_block = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("Host ") and "github.com" in stripped:
                    in_github_block = True
                    continue
                
                if in_github_block:
                    if stripped.startswith("Host "): 
                        in_github_block = False
                    elif stripped.lower().startswith("identityfile"):
                        # Found it: IdentityFile /path/to/key
                        parts = stripped.split(maxsplit=1)
                        if len(parts) > 1:
                            return os.path.expanduser(parts[1])
        except:
            pass
        return None

    def update_ssh_config(self, identity_file_path: str):
        """
        Updates the Host github.com block in ~/.ssh/config to use the specified identity file.
        Uses a marker strategy or full replacement of the github.com block.
        """
        if not os.path.exists(self.ssh_dir):
            os.makedirs(self.ssh_dir)
        
        # Verify identity file exists
        if not os.path.exists(identity_file_path):
            return False, f"Identity file not found at: {identity_file_path}"
        
        # Read existing config
        lines = []
        if os.path.exists(self.ssh_config_path):
            with open(self.ssh_config_path, 'r') as f:
                lines = f.readlines()
        
        # We will parse and reconstruct the file, replacing the github.com block
        new_lines = []
        in_github_block = False
        github_block_found = False
        
        # Define our standard block
        github_block = [
            f"Host github.com\n",
            f"    HostName github.com\n",
            f"    User git\n",
            f"    IdentityFile {identity_file_path}\n",
            f"    IdentitiesOnly yes\n"
        ]

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Host ") and "github.com" in stripped and not "bitbucket" in stripped: # Simple detection
                in_github_block = True
                github_block_found = True
                new_lines.extend(github_block)
                continue
            
            if in_github_block:
                if stripped.startswith("Host "): # Next block started
                    in_github_block = False
                    new_lines.append(line)
                else:
                    # Skip lines inside the old github block
                    pass
            else:
                new_lines.append(line)
        
        if not github_block_found:
            # Append to end if not found
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            new_lines.extend(github_block)
            
        try:
            # Backup first
            if os.path.exists(self.ssh_config_path):
                shutil.copy2(self.ssh_config_path, self.ssh_config_path + ".bak")
            
            with open(self.ssh_config_path, 'w') as f:
                f.writelines(new_lines)
            return True, "SSH config updated."
        except Exception as e:
            return False, f"Failed to write SSH config: {e}"

    def activate_account(self, name: str, email: str, ssh_key_path: str, gpg_key_id: str = None):
        """Orchestrates the switch."""
        # 1. Update Git Config
        git_ok, git_msg = self.set_global_git_user(name, email, gpg_key_id)
        if not git_ok:
            return False, git_msg
            
        # 2. Update SSH Config
        ssh_ok, ssh_msg = self.update_ssh_config(ssh_key_path)
        if not ssh_ok:
            return False, ssh_msg
            
        return True, f"Switched to {name} ({email})"

    def test_ssh_connection(self) -> str:
        """
        Runs ssh -T git@github.com to verify connection and identify string.
        Returns the raw output.
        """
        try:
            # ssh -T returns exit code 1 on success "Hi username...", so we must catch that.
            # actually, sometimes it returns 1 even if successful because 'shells are not allowed'.
            result = subprocess.run(
                ["ssh", "-T", "git@github.com"], 
                text=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            # GitHub usually writes the welcome message to stderr!
            output = result.stderr + result.stdout
            return output.strip()
        except Exception as e:
            return f"Error running ssh check: {str(e)}"
