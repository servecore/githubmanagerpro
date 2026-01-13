# GitHub Account Manager Pro

A powerful, modern desktop application for Windows to manage multiple GitHub accounts seamlessly. Switch between personal, work, and freelance identities with a single click, ensuring your commits are always attributed to the right user.

<img src="denastech.png" alt="App Icon" width="120">

## ✨ Key Features

*   **One-Click Account Switching**: Automatically updates global `git config` and `~/.ssh/config` to use the correct IdentityFile.
*   **SSH Key Management**: Generate new ED25519 SSH keys directly within the app or import existing ones.
*   **Per-Repository Configuration**: Bind specific project folders to specific accounts. The app enforces `local` git config for these folders, overriding global settings.
*   **GPG Signing Support**: Toggle GPG signing on/off per account to ensure your commits get the "Verified" badge on GitHub.
*   **Modern UI**: Built with `CustomTkinter` for a sleek, dark/light mode adaptable interface. Includes Profile Avatars fetched automatically from GitHub.
*   **System Tray Integration**: Minimize the app to the tray to keep it running in the background without cluttering your taskbar.
*   **Reliability**: Includes connection testing tools and robust error logging.

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/servecore/githubmanagerpro.git
    cd githubmanagerpro
    ```

2.  **Install Dependencies**
    Ensure you have Python 3.10+ installed.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Application**
    ```bash
    cd src
    python main.py
    ```

## � Prerequisites (For GPG Signing)

To use the **GPG Signing** feature, you must have GPG installed on your Windows machine. This app configures Git to use your keys, but you must create them first.

1.  **Install Gpg4win**: Download and install from [gpg4win.org](https://www.gpg4win.org/).
2.  **Generate a Key**:
    Open PowerShell and run:
    ```bash
    gpg --full-generate-key
    ```
    *   Select kind of key: **(1) RSA and RSA**
    *   Keysize: **4096**
    *   Validity: **0** (does not expire)
    *   Enter your **Real Name** and **Email** (must match GitHub account).
    *   Enter a **Passphrase** (optional but recommended).

3.  **Get Key ID**:
    List your keys:
    ```bash
    gpg --list-secret-keys --keyid-format LONG
    ```
    Copy the ID string (e.g., `3AA5C34371567BD2`) and use it in the **Add Account** dialog.

## �📖 User Guide

### 1. Adding an Account
1.  Click **Add Account** in the sidebar.
2.  **Alias**: A friendly name (e.g., "Work", "Personal").
3.  **username/email**: Your GitHub credentials.
4.  **SSH Key Path**: 
    *   Browse for an existing private key.
    *   **OR** Click "✨ Generate New SSH Key" to create one instantly.
5.  **GPG Key ID (Optional)**: If you use GPG, enter your Key ID here (e.g., `3AA5C34...`).
    *   *Note*: Leave blank if you don't use GPG.

### 2. Switching Accounts (Global)
1.  Select an account from the sidebar list.
2.  Click **ACTIVATE GLOBALLY** in the Dashboard tab.
3.  The status bar at the top will update to show the currently active identity.
4.  (Optional) Click **Test Connection** to verify SSH connectivity to GitHub.
5.  **Test GPG Signing**:
    *   Open a terminal.
    *   Run `git config --global user.signingkey` (Should match your Key ID).
    *   Run `git config --global commit.gpgsign` (Should be `true`).
    *   Make a test commit: `git commit --allow-empty -m "Test Signing"`.
    *   Verify signature: `git log --show-signature -1`.

### 3. Managing Repositories (Local Override)
Use this if you want specific folders to *always* use a specific account, regardless of the global setting.
1.  Go to the **Repository Manager** tab.
2.  Click **+ Add Repository**.
3.  Select the folder of your local git project.
4.  Choose which account should own this repo.
5.  **Done!** The app has configured `git config --local` for that folder.

### 4. System Tray
*   Click the **X** button on the window to minimize to the System Tray.
*   Double-click the tray icon to restore.
*   Right-click the icon -> **Quit** to exit completely.

## ⚠️ Notes
*   **Security**: This app stores paths to keys, not the keys themselves. However, `accounts.json` contains your email and potential GPG IDs in plain text.
*   **Windows**: Designed primarily for Windows (PowerShell/CMD compatibility).
*   **Logs**: If you encounter issues, check the `logs/` folder in the project root.

## 🤝 Contributing
Feel free to open issues or pull requests to improve the application!

---
**Created with ❤️ by DenasTech**

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
