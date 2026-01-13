import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import logging
import traceback
from datetime import datetime
import threading
from PIL import Image
import pystray
from pystray import MenuItem as item
from account_manager import AccountManager
from ssh_manager import GitSwitcher
from avatar_manager import AvatarManager
from repository_manager import RepositoryManager
from gpg_manager import GPGManager

# Setup Logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set Theme

# Set Theme
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GitHub Account Manager Pro")
        self.geometry("900x650")
        
        # Managers
        self.account_manager = AccountManager()
        self.git_switcher = GitSwitcher()
        
        # Local Keys Directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.local_keys_dir = os.path.join(project_root, "ssh_keys")
        self.avatars_dir = os.path.join(project_root, "avatars")
        self.icon_path = os.path.join(project_root, "denastech.png")
        
        # Managers
        self.avatar_manager = AvatarManager(self.avatars_dir)
        self.repo_manager = RepositoryManager()
        self.gpg_manager = GPGManager()

        # System Tray State
        self.tray_icon = None

        # UI Setup
        self.setup_ui()
        self.refresh_account_list()
        self.update_status_bar()
        
        self.current_dialog = None
        
        # Override Close Event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """Minimize to tray instead of closing."""
        self.withdraw()
        threading.Thread(target=self.create_tray_icon, daemon=True).start()

    def create_tray_icon(self):
        try:
            image = Image.open(self.icon_path)
            menu = (
                item("Make Active", self.show_window, default=True),
                item("Quit", self.quit_app)
            )
            self.tray_icon = pystray.Icon("name", image, "GitHub Manager", menu)
            self.tray_icon.run()
        except Exception as e:
            logging.error(f"Failed to create tray icon: {e}")
            self.quit_app() # Fallback

    def show_window(self, icon=None, item=None):
        """Restore window from tray."""
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        
        self.after(0, self.deiconify)

    def quit_app(self, icon=None, item=None):
        """Completely exit application."""
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.after(0, self.destroy_and_exit)

    def destroy_and_exit(self):
        self.destroy()
        os._exit(0) # Force kill threads

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # -- Sidebar (Left) --
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Git Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.btn_add = ctk.CTkButton(self.sidebar_frame, text="Add Account", command=self.show_add_dialog)
        self.btn_add.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_import = ctk.CTkButton(self.sidebar_frame, text="Import Current", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.import_current_account)
        self.btn_import.grid(row=2, column=0, padx=20, pady=10)
        
        # Account List Scrollable
        self.lbl_accounts = ctk.CTkLabel(self.sidebar_frame, text="SAVED ACCOUNTS", anchor="w")
        self.lbl_accounts.grid(row=3, column=0, padx=20, pady=(10, 0))
        
        self.scroll_accounts = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="")
        self.scroll_accounts.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        self.scroll_accounts.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")
        
        # -- Main Area (Right) --
        # Use Tabview
        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=1, rowspan=4, padx=20, pady=10, sticky="nsew")
        
        self.tab_dashboard = self.tab_view.add("Dashboard")
        self.tab_repos = self.tab_view.add("Repository Manager")
        
        # === DASHBOARD TAB ===
        self.setup_dashboard_tab()
        
        # === REPO MANAGER TAB ===
        self.setup_repo_tab()

    def setup_dashboard_tab(self):
        # Header
        self.header_frame = ctk.CTkFrame(self.tab_dashboard, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=10)
        
        self.lbl_current_title = ctk.CTkLabel(self.header_frame, text="Current Global Identity", font=ctk.CTkFont(size=14))
        self.lbl_current_title.pack(anchor="w")
        
        self.lbl_current_user = ctk.CTkLabel(self.header_frame, text="Loading...", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_current_user.pack(side="left", pady=(5,0))
        
        self.btn_verify = ctk.CTkButton(self.header_frame, text="Test Connection", width=100, command=self.test_connection, fg_color="#2CC985", hover_color="#229C68")
        self.btn_verify.pack(side="right")

        # Details Area
        self.details_frame = ctk.CTkFrame(self.tab_dashboard)
        self.details_frame.pack(fill="both", expand=True, pady=20)
        
        self.lbl_details_title = ctk.CTkLabel(self.details_frame, text="Select an account", font=ctk.CTkFont(size=24, weight="bold"))
        self.lbl_details_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        self.details_grid = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        self.details_grid.pack(fill="x", padx=20)
        
        self.lbl_det_alias = self.create_detail_row(self.details_grid, "Alias:", 0)
        self.lbl_det_username = self.create_detail_row(self.details_grid, "Username:", 1)
        self.lbl_det_email = self.create_detail_row(self.details_grid, "Email:", 2)
        self.lbl_det_email = self.create_detail_row(self.details_grid, "Email:", 2)
        self.lbl_det_key = self.create_detail_row(self.details_grid, "SSH Key:", 3)
        self.lbl_det_gpg = self.create_detail_row(self.details_grid, "GPG Key:", 4)
        
        self.btn_activate = ctk.CTkButton(self.details_frame, text="ACTIVATE GLOBALLY", height=50, font=ctk.CTkFont(size=16, weight="bold"), state="disabled", command=self.activate_selected_account)
        self.btn_activate.pack(pady=40, padx=20, fill="x")
        
        btn_action_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        btn_action_frame.pack(pady=(0, 20))
        
        self.btn_edit = ctk.CTkButton(btn_action_frame, text="Edit Account", width=120, height=35, state="disabled", command=self.edit_account)
        self.btn_edit.pack(side="left", padx=10)
        
        self.btn_delete = ctk.CTkButton(btn_action_frame, text="Delete Account", width=120, height=35, fg_color="#FF5555", hover_color="#CC0000", state="disabled", command=self.delete_account)
        self.btn_delete.pack(side="left", padx=10)

    def setup_repo_tab(self):
        # Top Bar
        top_bar = ctk.CTkFrame(self.tab_repos, fg_color="transparent")
        top_bar.pack(fill="x", pady=10)
        
        ctk.CTkLabel(top_bar, text="Managed Repositories (Local Overrides)", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(top_bar, text="+ Add Repository", command=self.add_repository).pack(side="right")
        
        # Scrollable List
        self.scroll_repos = ctk.CTkScrollableFrame(self.tab_repos)
        self.scroll_repos.pack(fill="both", expand=True, pady=10)
        
        self.refresh_repo_list()

    def refresh_repo_list(self):
        for widget in self.scroll_repos.winfo_children():
            widget.destroy()
            
        repos = self.repo_manager.get_repos()
        if not repos:
            ctk.CTkLabel(self.scroll_repos, text="No repositories managed yet.", text_color="gray").pack(pady=20)
            return

        for repo in repos:
            # Find account name
            acc_name = "Unknown"
            acc = self.account_manager.get_account_by_id(repo['account_id'])
            if acc:
                acc_name = acc['alias']
                
            card = ctk.CTkFrame(self.scroll_repos)
            card.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(card, text=repo['alias'], font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(card, text=repo['path'], text_color="gray").pack(side="left", padx=10)
            
            ctk.CTkButton(card, text="Delete", width=60, fg_color="#FF5555", hover_color="#CC0000", 
                          command=lambda p=repo['path']: self.delete_repo(p)).pack(side="right", padx=10, pady=5)
            
            ctk.CTkLabel(card, text=f"Bound to: {acc_name}", text_color="#3B8ED0").pack(side="right", padx=10)

    def add_repository(self):
        path = filedialog.askdirectory(title="Select Repository Folder")
        if not path:
            return
            
        if not os.path.exists(os.path.join(path, ".git")):
             messagebox.showerror("Invalid Repo", "The selected folder is not a git repository (missing .git).")
             return

        # Ask user which account to bind
        accounts = self.account_manager.get_accounts()
        if not accounts:
             messagebox.showinfo("No Accounts", "Please add GitHub accounts first.")
             return
             
        aliases = [f"{a['alias']} ({a['username']})" for a in accounts]
        
        # Simple Dialog to pick account
        dialog = ctk.CTkToplevel(self)
        dialog.title("Bind Repository")
        dialog.geometry("400x200")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="Select Account for this Repo:", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        combo = ctk.CTkComboBox(dialog, values=aliases)
        combo.pack(pady=10)
        
        def confirm():
            selection = combo.get()
            if not selection: return
            
            # Match back to account
            idx = aliases.index(selection)
            acc = accounts[idx]
            
            folder_name = os.path.basename(path)
            
            # 1. Update Git Local Config
            success, msg = self.git_switcher.set_local_git_user(path, acc['username'], acc['email'], acc['ssh_key_path'])
            if not success:
                 messagebox.showerror("Git Error", msg)
                 return
                 
            # 2. Save to DB
            self.repo_manager.add_repo(path, folder_name, acc['id'])
            self.refresh_repo_list()
            messagebox.showinfo("Success", f"Repository '{folder_name}' is now bound to {acc['alias']}!")
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Bind Account", command=confirm).pack(pady=20)

    def delete_repo(self, path):
        if messagebox.askyesno("Confirm", "Stop managing this repository? (Git config will remain as is)"):
            self.repo_manager.remove_repo(path)
            self.refresh_repo_list()


    def create_detail_row(self, parent, label_text, row):
        ctk.CTkLabel(parent, text=label_text, font=ctk.CTkFont(weight="bold")).grid(row=row, column=0, sticky="w", pady=5)
        lbl = ctk.CTkLabel(parent, text="-")
        lbl.grid(row=row, column=1, sticky="w", padx=20, pady=5)
        return lbl

    def refresh_account_list(self):
        # Clear scrollable frame
        for widget in self.scroll_accounts.winfo_children():
            widget.destroy()
            
        self.accounts_cache = self.account_manager.get_accounts()
        self.account_buttons = []
        
        for idx, acc in enumerate(self.accounts_cache):
            # Load if exists immediately
            avatar_img = self.avatar_manager.load_avatar_image(acc['username'])
            
            # If not exists, trigger fetch in background (silent, no callback spam)
            if not avatar_img:
                 self.avatar_manager.fetch_avatar(acc['username'], self.on_single_avatar_downloaded)

            btn = ctk.CTkButton(self.scroll_accounts, text=f"  {acc['alias']}", 
                                image=avatar_img,
                                compound="left",
                                anchor="w",
                                height=50,
                                command=lambda i=idx: self.on_account_select(i),
                                fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
            btn.pack(pady=5, fill="x")
            self.account_buttons.append(btn)
        
        self.update_status_bar()

    def on_single_avatar_downloaded(self, username, path):
        # Determine if we need to refresh.
        # To avoid refreshing the WHOLE list for every single image,
        # we check if we are already in a refresh loop or simply schedule one refresh in 1s.
        if not hasattr(self, '_refresh_pending') or not self._refresh_pending:
            self._refresh_pending = True
            self.after(1000, self.perform_delayed_refresh)

    def perform_delayed_refresh(self):
        self._refresh_pending = False
        self.refresh_account_list() 

    def update_status_bar(self):
        name, email = self.git_switcher.get_current_global_user()
        if name and email:
            # Try to match name/email to an account to get username for avatar
            # This is a bit loose because git config doesn't store 'username', only name.
            # But we can try to find email in our DB
            found_img = None
            for acc in self.accounts_cache:
                if acc['email'] == email:
                    self.avatar_manager.fetch_avatar(acc['username'], None)
                    found_img = self.avatar_manager.load_avatar_image(acc['username'], size=(60,60))
                    break
            
            self.lbl_current_user.configure(text=f"  {name}\n  <{email}>", image=found_img, compound="left", text_color="#3B8ED0")
        else:
            self.lbl_current_user.configure(text="Not configured", image=None, text_color="gray")

    def on_account_select(self, index):
        # Reset buttons style
        for btn in self.account_buttons:
             btn.configure(fg_color="transparent")
        
        # Highlight selected
        self.account_buttons[index].configure(fg_color=("gray75", "gray25"))
        
        account = self.accounts_cache[index]
        self.selected_account = account
        
        self.lbl_details_title.configure(text=account['alias'])
        self.lbl_det_alias.configure(text=account['alias'])
        self.lbl_det_username.configure(text=account['username'])
        self.lbl_det_email.configure(text=account['email'])
        self.lbl_det_email.configure(text=account['email'])
        self.lbl_det_key.configure(text=account['ssh_key_path'])
        
        gpg_txt = account.get('gpg_key_id', 'Not Set')
        if not gpg_txt: gpg_txt = 'Not Set'
        if not gpg_txt: gpg_txt = 'Not Set'
        self.lbl_det_gpg.configure(text=gpg_txt)
        
        self.btn_activate.configure(state="normal")
        self.btn_edit.configure(state="normal")
        self.btn_delete.configure(state="normal")

    def show_add_dialog(self):
        if self.current_dialog is None or not self.current_dialog.winfo_exists():
            self.current_dialog = AddAccountDialog(self)
        else:
            self.current_dialog.focus()
            self.current_dialog.lift()

    def edit_account(self):
        if not hasattr(self, 'selected_account'):
            return
            
        if self.current_dialog is None or not self.current_dialog.winfo_exists():
            self.current_dialog = AddAccountDialog(self, account_to_edit=self.selected_account)
        else:
            self.current_dialog.focus()
            self.current_dialog.lift()

    def delete_account(self):
        if not hasattr(self, 'selected_account'):
            return
            
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {self.selected_account['alias']}?"):
            self.account_manager.delete_account(self.selected_account['id'])
            self.refresh_account_list()
            # Clear details
            self.lbl_details_title.configure(text="Select an account")
            self.btn_activate.configure(state="disabled")
            self.btn_edit.configure(state="disabled")
            self.btn_delete.configure(state="disabled")

    def import_current_account(self):
        name, email = self.git_switcher.get_current_global_user()
        if not name or not email:
            messagebox.showerror("Error", "No global git user configured found.")
            return
            
        ssh_key = self.git_switcher.get_current_ssh_identity()
        if not ssh_key:
            # Check if likely using HTTPS
            if self.git_switcher.check_if_using_https():
                msg = (
                    "Akun saat ini terdeteksi menggunakan HTTPS/Token.\n\n"
                    "Aplikasi ini menggunakan SSH Key untuk fitur One-Click Switch.\n"
                    "Agar akun ini bisa dimanage, kita perlu membuatkan SSH Key baru.\n\n"
                    "Lanjut untuk menambahkan akun ini dan Generate SSH Key?"
                )
                if messagebox.askyesno("HTTPS Detected", msg):
                    # Open Add Dialog Prefilled
                    dlg = AddAccountDialog(self)
                    # Suggest an alias based on username or "Existing"
                    alias_guess = name if name else "Existing Account"
                    dlg.ent_alias.insert(0, alias_guess)
                    dlg.ent_username.insert(0, name)
                    dlg.ent_email.insert(0, email)
                    return
                else:
                    return

            ssh_key = messagebox.askyesno("SSH Key Not Found", 
                "Could not detect IdentityFile in ~/.ssh/config for github.com.\n\n"
                "Do you want to use the default '~/.ssh/id_rsa'?")
            if ssh_key:
                ssh_key = os.path.expanduser("~/.ssh/id_rsa")
            else:
                ssh_key = filedialog.askopenfilename(title="Select SSH Key for this Current Account")
        
        if not ssh_key:
            return

        # Pop up dialog pre-filled
        if self.current_dialog is None or not self.current_dialog.winfo_exists():
            dlg = AddAccountDialog(self)
            self.current_dialog = dlg
        else:
             dlg = self.current_dialog
             dlg.focus()
             dlg.lift()
             # If reusing, we might need to clear/reset logic, but for Import scenario, 
             # usually we assume user isn't doing other things. 
             # For safety, let's just use the active dialog.
             
        dlg.ent_alias.delete(0, tk.END) # Clear previous if any
        dlg.ent_alias.insert(0, "Current Profile")
        dlg.ent_username.insert(0, name)
        dlg.ent_email.insert(0, email)
        dlg.ent_key.delete(0, tk.END)
        dlg.ent_key.insert(0, ssh_key)

    def test_connection(self):
        self.btn_verify.configure(text="Testing...", state="disabled")
        self.update()
        result = self.git_switcher.test_ssh_connection()
        self.btn_verify.configure(text="Test Connection", state="normal")
        
        if "successfully authenticated" in result:
             messagebox.showinfo("Connection Success", f"GitHub Response:\n\n{result}")
        else:
             messagebox.showwarning("Connection Issue", f"GitHub Response:\n\n{result}")

    def activate_selected_account(self):
        if not hasattr(self, 'selected_account'):
            return
            
        acc = self.selected_account
        gpg_id = acc.get('gpg_key_id', None)
        success, msg = self.git_switcher.activate_account(acc['alias'], acc['email'], acc['ssh_key_path'], gpg_id)
        
        if success:
            messagebox.showinfo("Success", f"Active identity switched to:\n{acc['alias']}\n{acc['email']}")
            self.update_status_bar()
        else:
            messagebox.showerror("Error", msg)

class AddAccountDialog(ctk.CTkToplevel):
    def __init__(self, parent, account_to_edit=None):
        super().__init__(parent)
        self.parent = parent
        self.account_to_edit = account_to_edit
        
        title = "Edit Account" if account_to_edit else "Add New Account"
        self.title(title)
        self.geometry("500x550")
        
        self.setup_form()
        
        if account_to_edit:
            self.ent_alias.insert(0, account_to_edit['alias'])
            self.ent_username.insert(0, account_to_edit['username'])
            self.ent_email.insert(0, account_to_edit['email'])
            self.ent_key.insert(0, account_to_edit['ssh_key_path'])
            gpg = account_to_edit.get('gpg_key_id', '')
            if gpg: self.ent_gpg.insert(0, gpg)
        
        # Bring to front
        self.attributes("-topmost", True)
        
    def setup_form(self):
        self.grid_columnconfigure(0, weight=1)
        
        title_txt = "Edit Account" if self.account_to_edit else "Add New Account"
        ctk.CTkLabel(self, text=title_txt, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        frm = ctk.CTkFrame(self)
        frm.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frm, text="Alias (e.g. Work)").pack(anchor="w", padx=10, pady=(10,0))
        self.ent_alias = ctk.CTkEntry(frm)
        self.ent_alias.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(frm, text="GitHub Username").pack(anchor="w", padx=10)
        self.ent_username = ctk.CTkEntry(frm)
        self.ent_username.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(frm, text="Email").pack(anchor="w", padx=10)
        self.ent_email = ctk.CTkEntry(frm)
        self.ent_email.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(frm, text="SSH Private Key Path").pack(anchor="w", padx=10)
        key_frm = ctk.CTkFrame(frm, fg_color="transparent")
        key_frm.pack(fill="x", padx=10, pady=(0, 10))
        
        self.ent_key = ctk.CTkEntry(key_frm)
        self.ent_key.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(key_frm, text="Browse", width=60, command=self.browse_key).pack(side="left", padx=(5, 0))
        
        ctk.CTkLabel(frm, text="GPG Key ID (Optional)").pack(anchor="w", padx=10)
        gpg_frm = ctk.CTkFrame(frm, fg_color="transparent")
        gpg_frm.pack(fill="x", padx=10, pady=(0, 10))
        
        self.ent_gpg = ctk.CTkEntry(gpg_frm, placeholder_text="e.g. 3AA5C34371567BD2")
        self.ent_gpg.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(gpg_frm, text="Generate", width=80, fg_color="#E0AA00", hover_color="#C09000", text_color="black", command=self.generate_gpg).pack(side="left", padx=(5,0))
        
        # Generator Button
        ctk.CTkButton(frm, text="✨ Generate New SSH Key", command=self.generate_key, fg_color="#E0AA00", hover_color="#C09000", text_color="black").pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self, text="Save Account", command=self.save, font=ctk.CTkFont(weight="bold")).pack(pady=20, padx=20, fill="x")
    
    def generate_key(self):
        alias = self.ent_alias.get().strip()
        email = self.ent_email.get().strip()
        
        if not alias or not email:
            messagebox.showwarning("Required Information", "Please enter an Alias and Email first to generate a specific key.")
            self.attributes("-topmost", False) # Release focus to msgbox
            return
            
        # Suggest filename
        safe_alias = "".join([c for c in alias if c.isalnum() or c in ('-', '_')]).lower()
        filename = f"id_ed25519_{safe_alias}"
        
        if messagebox.askyesno("Generate Key", f"Generate new SSH key '{filename}' for {email}?\n\nLocation: {self.parent.local_keys_dir}"):
            success, msg, pub_key = self.parent.git_switcher.generate_ssh_key(email, filename, output_dir=self.parent.local_keys_dir)
            if success:
                # Show Public Key and instructions
                self.show_pubkey_dialog(pub_key)
                
                # Auto fill path
                full_path = os.path.join(self.parent.local_keys_dir, filename)
                self.ent_key.delete(0, tk.END)
                self.ent_key.insert(0, full_path)
            else:
                messagebox.showerror("Generation Failed", msg)

    def generate_gpg(self):
        # Validation
        name = self.ent_username.get().strip() # GPG prefers user.name usually
        email = self.ent_email.get().strip()
        
        if not name or not email:
             messagebox.showwarning("Missing Info", "Please fill Username and Email fields first.")
             return
             
        if not self.parent.gpg_manager.is_gpg_installed():
             messagebox.showerror("GPG Not Found", "GPG does not appear to be installed (gpg not in PATH).\nPlease install Gpg4win first.")
             return

        # Ask for passphrase
        passphrase = ctk.CTkInputDialog(text="Enter a Passphrase to protect your new GPG Key:\n(Required)", title="GPG Passphrase").get_input()
        if not passphrase:
             return
             
        confirm = ctk.CTkInputDialog(text="Confirm Passphrase:", title="Confirm Passphrase").get_input()
        if passphrase != confirm:
             messagebox.showerror("Mismatch", "Passphrases do not match.")
             return

        self.attributes("-topmost", False) # Release focus during heavy process
        self.parent.update_idletasks()
        
        # Show loading (simple blocking for now, ideally threaded)
        # threading this is better but sticking to simple for stability as per user pref
        messagebox.showinfo("Generating", "Generating GPG Key... This may take a minute.\nClick OK to start.")
        
        success, msg, key_id, pub_key = self.parent.gpg_manager.generate_gpg_key(name, email, passphrase)
        
        self.attributes("-topmost", True)
        
        if success:
             self.ent_gpg.delete(0, tk.END)
             self.ent_gpg.insert(0, key_id)
             self.show_pubkey_dialog(pub_key, key_type="GPG")
        else:
             messagebox.showerror("GPG Error", msg)

    def show_pubkey_dialog(self, pub_key, key_type="SSH"):
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"{key_type} Public Key Generated")
        dlg.geometry("600x450")
        dlg.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(dlg, text=f"Key generated successfully!\n\nCOPY this public key and add it to GitHub:\n(Settings -> SSH and GPG keys -> New {key_type} key)", wraplength=580)
        lbl.pack(pady=20,padx=20)
        
        txt = ctk.CTkTextbox(dlg, height=150, width=500)
        txt.pack(padx=20, pady=10)
        txt.insert("0.0", pub_key)
        txt.configure(state="disabled") # Read-only
        
        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def copy_to_clipboard():
            dlg.clipboard_clear()
            dlg.clipboard_append(pub_key)
            messagebox.showinfo("Copied", "Public key copied to clipboard!")
            
        ctk.CTkButton(btn_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Close", command=dlg.destroy, fg_color="gray").pack(side="left", padx=10)

    def browse_key(self):
        filename = filedialog.askopenfilename(title="Select SSH Private Key")
        if filename:
            self.ent_key.delete(0, tk.END)
            self.ent_key.insert(0, filename)
            
    def save(self):
        alias = self.ent_alias.get().strip()
        username = self.ent_username.get().strip()
        email = self.ent_email.get().strip()
        key_path = self.ent_key.get().strip()
        gpg_key = self.ent_gpg.get().strip()
        
        if not all([alias, username, email, key_path]):
            messagebox.showwarning("Missing Data", "All fields are required.")
            self.attributes("-topmost", False)
            return

        # Basic verification that key exists
        if not os.path.exists(key_path):
             messagebox.showwarning("Invalid Key", "The SSH key file does not exist.")
             self.attributes("-topmost", False)
             return
             
             self.attributes("-topmost", False)
             return
             
        if self.account_to_edit:
            self.parent.account_manager.update_account(self.account_to_edit['id'], alias, username, email, key_path, gpg_key)
        else:
            self.parent.account_manager.add_account(alias, username, email, key_path, gpg_key)
            
        self.parent.refresh_account_list()
        self.destroy()


    def report_callback_exception(self, exc, val, tb):
        """Global Error Handler for Tkinter Event Loop"""
        error_msg = "".join(traceback.format_exception(exc, val, tb))
        logging.error(f"Uncaught Exception:\n{error_msg}")
        messagebox.showerror("Application Error", f"An unexpected error occurred:\n\n{val}\n\nSee logs for details.")

if __name__ == "__main__":
    try:
        app = App()
        # Hook the exception handler to the underlying tk instance
        app.report_callback_exception = app.report_callback_exception
        app.mainloop()
    except Exception as e:
        # Catch errors occurring before mainloop
        error_msg = "".join(traceback.format_exc())
        logging.critical(f"Critical Startup Error:\n{error_msg}")
        # Try to show a message box if tk is initialized, otherwise print
        try:
             messagebox.showerror("Critical Error", f"Failed to start application:\n{str(e)}")
        except:
             print(f"Critical Error: {e}")
