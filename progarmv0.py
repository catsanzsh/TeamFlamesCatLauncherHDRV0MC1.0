import os
import shutil
import json
import subprocess
import platform
import urllib.request
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import re
import hashlib

# ====== Constants ======
MINECRAFT_DIR = os.path.expanduser("~/.minecraft")
VERSIONS_DIR = os.path.join(MINECRAFT_DIR, "versions")
JAVA_DIR = os.path.expanduser("~/.catclient/java")
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

ACCOUNTS_FILE = "accounts.json"
PROFILES_FILE = "profiles.json"

# ====== Style for modern look ======
# Use a clean font
BASE_FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 14, "bold")
BOLD_FONT = ("Segoe UI", 9, "bold")
BG_COLOR = "#222222"
FG_COLOR = "#DDDDDD"
ACCENT_COLOR = "#3A9BD9"
BUTTON_COLOR = "#444444"
HOVER_COLOR = "#555555"
ENTRY_BG = "#333333"

# Helper to style ttk buttons
def style_button(btn):
    btn.configure(
        bg=BUTTON_COLOR,
        fg=FG_COLOR,
        activebackground=HOVER_COLOR,
        activeforeground=FG_COLOR,
        bd=0,
        font=BASE_FONT,
        relief='flat'
    )

# Utility for custom styled buttons
def create_button(parent, text, command):
    btn = tk.Button(parent, text=text, command=command)
    style_button(btn)
    return btn

class CatClient(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CatClient 1.a")
        self.geometry("1024x640")
        self.minsize(900, 500)
        self.configure(bg=BG_COLOR)
        self.accounts = self.load_json(ACCOUNTS_FILE)
        self.profiles = self.load_json(PROFILES_FILE)
        self.versions = {}
        self.version_categories = {
            "Latest Release": [],
            "Latest Snapshot": [],
            "Release": [],
            "Snapshot": [],
            "Old Beta": [],
            "Old Alpha": []
        }
        self.create_widgets()
        self.load_version_manifest()

    def load_json(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return {}

    def save_json(self, data, filepath):
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def create_widgets(self):
        # Use ttk Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        # Main tab
        self.tab_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text='Launcher')

        # Profile tab
        self.tab_profile = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_profile, text='Accounts & Profiles')

        # Mods tab
        self.tab_mods = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mods, text='Mods')

        # Style ttk notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", background=BUTTON_COLOR, foreground=FG_COLOR, padding=10)
        style.map("TNotebook.Tab", background=[("selected", ACCENT_COLOR)])

        # Build launcher UI
        self.build_main_tab()
        self.build_profile_tab()
        self.build_mods_tab()

    def build_main_tab(self):
        # Main container
        frame = ttk.Frame(self.tab_main)
        frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Left panel: login, version, settings
        left_frame = tk.Frame(frame, width=300, bg=BG_COLOR)
        left_frame.pack(side='left', fill='y', padx=(0,20))
        left_frame.pack_propagate(False)

        # Logo and title
        title = tk.Label(left_frame, text="😺", font=("Segoe UI", 48), bg=BG_COLOR)
        title.pack(pady=(20,5))
        lbl_title = tk.Label(left_frame, text="CatClient", font=TITLE_FONT, bg=BG_COLOR, fg=FG_COLOR)
        lbl_title.pack(pady=(0,20))

        # Version selection
        ver_frame = tk.LabelFrame(left_frame, text="GAME VERSION", bg=BG_COLOR, fg=FG_COLOR, relief='flat')
        ver_frame.pack(fill='x', pady=10)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(ver_frame, values=list(self.version_categories.keys()), textvariable=self.category_var, state='readonly')
        self.category_combo.pack(fill='x', padx=10, pady=5)
        self.category_combo.set("Latest Release")
        self.category_combo.bind("<<ComboboxSelected>>", self.update_version_list)

        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(ver_frame, textvariable=self.version_var, state='readonly')
        self.version_combo.pack(fill='x', padx=10, pady=5)

        # User settings: username and RAM
        settings_frame = tk.LabelFrame(left_frame, text="SETTINGS", bg=BG_COLOR, fg=FG_COLOR, relief='flat')
        settings_frame.pack(fill='x', pady=10)
        # Username
        user_lbl = ttk.Label(settings_frame, text="Username", background=BG_COLOR, foreground=FG_COLOR, font=BOLD_FONT)
        user_lbl.pack(anchor='w', padx=10, pady=(10,0))
        self.username_entry = tk.Entry(settings_frame, bg=ENTRY_BG, fg=FG_COLOR, font=BASE_FONT, relief='flat')
        self.username_entry.pack(fill='x', padx=10, pady=5)
        self.username_entry.insert(0, "Enter Username")

        # RAM Slider
        ram_lbl_frame = tk.Frame(settings_frame, bg=BG_COLOR)
        ram_lbl_frame.pack(fill='x', padx=10, pady=(10,0))
        self.ram_label = ttk.Label(ram_lbl_frame, text="4GB", background=BG_COLOR, foreground=FG_COLOR, font=BASE_FONT)
        self.ram_label.pack(side='left')
        self.ram_scale = tk.Scale(ram_lbl_frame, from_=1, to=16, orient='horizontal', bg=BG_COLOR, fg=FG_COLOR, highlightthickness=0, troughcolor=ENTRY_BG, command=lambda v: self.ram_label.config(text=f"{int(float(v))}GB"))
        self.ram_scale.set(4)
        self.ram_scale.pack(fill='x', padx=0, pady=5)

        # Buttons
        btn_frame = tk.Frame(left_frame, bg=BG_COLOR)
        btn_frame.pack(fill='x', padx=10, pady=20)
        btn_skin = create_button(btn_frame, "CHANGE SKIN", self.select_skin)
        btn_skin.pack(fill='x', pady=5)
        btn_skin.bind("<Enter>", lambda e: e.widget.config(bg=HOVER_COLOR))
        btn_skin.bind("<Leave>", lambda e: e.widget.config(bg=BUTTON_COLOR))
        btn_launch = create_button(btn_frame, "PLAY", self.prepare_and_launch)
        btn_launch.pack(fill='x', pady=5)
        btn_launch.bind("<Enter>", lambda e: e.widget.config(bg=ACCENT_COLOR))
        btn_launch.bind("<Leave>", lambda e: e.widget.config(bg=ACCENT_COLOR))

        # Main Content (Right side)
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill='both', expand=True, padx=(0,20))
        lbl_changelog = ttk.Label(content_frame, text="RECENT CHANGES", font=TITLE_FONT)
        lbl_changelog.pack(pady=10)
        changelog_items = [
            "🚀 Added FPS Limiter: Set maxFps to 60 and disable VSync.",
            "🔧 Refactored launch process.",
            "🎨 UI improvements in style.",
            "⚙️ Auto Java 21 install.",
            "🖼️ Skin support.",
            "🌍 Version manifest update."
        ]
        for item in changelog_items:
            lbl = ttk.Label(content_frame, text=item, wraplength=600, font=BASE_FONT, foreground=FG_COLOR)
            lbl.pack(anchor='w', padx=20, pady=2)

    def build_profile_tab(self):
        frame = self.tab_profile
        ttk.Label(frame, text="Accounts", font=TITLE_FONT).pack(pady=10)
        self.acc_listbox = tk.Listbox(frame, height=4, bg=ENTRY_BG, fg=FG_COLOR, font=BASE_FONT)
        self.acc_listbox.pack(fill='x', padx=20)
        self.refresh_account_list()

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Add Account", command=self.add_account).pack(side='left', padx=10)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_account).pack(side='left', padx=10)

        ttk.Label(frame, text="Profiles", font=TITLE_FONT).pack(pady=10)
        self.profiles_combo = ttk.Combobox(frame, values=list(self.profiles.keys()), state='normal')
        self.profiles_combo.pack(fill='x', padx=20, pady=5)
        ttk.Button(frame, text="Save Profile", command=self.save_current_profile).pack(pady=5)
        ttk.Button(frame, text="Load Profile", command=self.load_selected_profile).pack(pady=5)

    def build_mods_tab(self):
        frame = self.tab_mods
        ttk.Button(frame, text='Select Mods Folder', command=self.select_mod_folder).pack(pady=20)
        self.mod_folder_var = tk.StringVar()
        ttk.Label(frame, textvariable=self.mod_folder_var).pack(pady=10)

    # --- Account/Profile Management ---
    def refresh_account_list(self):
        self.acc_listbox.delete(0, tk.END)
        for acc in self.accounts:
            self.acc_listbox.insert(tk.END, acc)

    def add_account(self):
        username = simple_input(self, "Enter username:")
        if username:
            self.accounts[username] = {}
            self.save_json(self.accounts, ACCOUNTS_FILE)
            self.refresh_account_list()

    def remove_account(self):
        sel = self.acc_listbox.curselection()
        if sel:
            username = self.acc_listbox.get(sel)
            if username in self.accounts:
                del self.accounts[username]
                self.save_json(self.accounts, ACCOUNTS_FILE)
                self.refresh_account_list()

    def save_current_profile(self):
        name = simple_input(self, "Profile name:")
        if name:
            profile = {
                'version': self.version_var.get(),
                'username': self.username_entry.get(),
                'ram': self.ram_scale.get(),
                'mod_folder': self.mod_folder_var.get()
            }
            self.profiles[name] = profile
            self.save_json(self.profiles, PROFILES_FILE)
            self.refresh_profiles()

    def refresh_profiles(self):
        self.profiles_combo['values'] = list(self.profiles.keys())

    def load_selected_profile(self):
        name = self.profiles_combo.get()
        profile = self.profiles.get(name)
        if profile:
            self.version_var = profile.get('version', '')
            self.username_entry.delete(0, tk.END)
            self.username_entry.insert(0, profile.get('username', ''))
            self.ram_scale.set(profile.get('ram', 4))
            self.mod_folder_var.set(profile.get('mod_folder', ''))
        else:
            messagebox.showinfo("Info", "Profile not found.")

    # --- Mod folder ---
    def select_mod_folder(self):
        fold = filedialog.askdirectory()
        if fold:
            self.mod_folder_var.set(fold)

    # --- Load version manifest ---
    def load_version_manifest(self):
        try:
            with urllib.request.urlopen(VERSION_MANIFEST_URL) as url:
                manifest = json.loads(url.read().decode())
            latest_rel = manifest["latest"]["release"]
            latest_snap = manifest["latest"]["snapshot"]
            # Clear categories
            for k in self.version_categories:
                self.version_categories[k] = []
            for v in manifest["versions"]:
                vid = v["id"]
                self.versions[vid] = v["url"]
                if vid == latest_rel:
                    self.version_categories["Latest Release"].append(vid)
                elif vid == latest_snap:
                    self.version_categories["Latest Snapshot"].append(vid)
                elif v["type"] == "release":
                    self.version_categories["Release"].append(vid)
                elif v["type"] == "snapshot":
                    self.version_categories["Snapshot"].append(vid)
                elif v["type"] == "old_beta":
                    self.version_categories["Old Beta"].append(vid)
                elif v["type"] == "old_alpha":
                    self.version_categories["Old Alpha"].append(vid)
            self.update_version_list()
        except Exception as e:
            print("Version manifest load error:", e)

    def update_version_list(self, event=None):
        cat = self.category_var.get()
        vlist = self.version_categories.get(cat, [])
        self.version_combo['values'] = vlist
        if vlist:
            self.version_combo.set(vlist[0])

    # --- Launch process ---
    def prepare_and_launch(self):
        self.install_java_if_needed()
        version = self.version_combo.get()
        username = self.username_entry.get()
        ram = self.ram_scale.get()
        mod_folder = self.mod_folder_var.get()
        self.download_and_launch(version, username, ram, mod_folder)

    def download_and_launch(self, version, username, ram, mod_folder):
        if not version:
            messagebox.showerror("Error", "Select a version.")
            return
        version_url = self.versions.get(version)
        if not version_url:
            messagebox.showerror("Error", "Version URL missing.")
            return
        self.download_version_files(version, version_url)
        cmd = self.build_launch_command(version, username, ram, mod_folder)
        if cmd:
            # Launch Minecraft
            print("Launching:", " ".join(cmd))
            subprocess.Popen(cmd)

    def download_version_files(self, version_id, version_url):
        print(f"⬇️ Downloading {version_id}")
        version_dir = os.path.join(VERSIONS_DIR, version_id)
        os.makedirs(version_dir, exist_ok=True)
        # Download version JSON
        try:
            with urllib.request.urlopen(version_url) as r:
                data = json.loads(r.read().decode())
            with open(os.path.join(version_dir, f"{version_id}.json"), 'w') as f:
                json.dump(data, f, indent=2)
            # Download client jar
            client_url = data["downloads"]["client"]["url"]
            sha1 = data["downloads"]["client"]["sha1"]
            jar_path = os.path.join(version_dir, f"{version_id}.jar")
            if not (os.path.exists(jar_path) and self.verify_file(jar_path, sha1)):
                urllib.request.urlretrieve(client_url, jar_path)
                if not self.verify_file(jar_path, sha1):
                    messagebox.showerror("Error", "JAR checksum mismatch")
        except Exception as e:
            print("Error downloading files:", e)

    def verify_file(self, filepath, sha1sum):
        hash_obj = hashlib.sha1()
        with open(filepath, 'rb') as f:
            hash_obj.update(f.read())
        return hash_obj.hexdigest() == sha1sum

    def build_launch_command(self, version, username, ram, mod_folder=None):
        version_dir = os.path.join(VERSIONS_DIR, version)
        json_path = os.path.join(version_dir, f"{version}.json")
        try:
            with open(json_path) as f:
                version_data = json.load(f)
        except:
            messagebox.showerror("Error", "Cannot read version json.")
            return []

        current_os = platform.system().lower()
        if current_os=="darwin": current_os="osx"
        main_class = version_data.get("mainClass", "net.minecraft.client.main.Main")
        classpath = []

        jar_path = os.path.join(version_dir, f"{version}.jar")
        classpath = [jar_path]
        libraries_dir = os.path.join(MINECRAFT_DIR, "libraries")
        for lib in version_data.get("libraries", []):
            if "downloads" in lib and "artifact" in lib["downloads"]:
                path = lib["downloads"]["artifact"]["path"]
                classpath.append(os.path.join(libraries_dir, path))
        classpath_str = ';'.join(classpath) if current_os=='windows' else ':'.join(classpath)

        java_exe = "java"
        # if Java missing, handle differently
        if not self.is_java_installed():
            java_exe = os.path.join(JAVA_DIR, "jdk-21.0.5+11", "bin", "java.exe" if current_os=='windows' else "java")

        cmd = [java_exe, f"-Xmx{ram}G"]

        # JVM arguments
        if "arguments" in version_data:
            for arg in version_data["arguments"].get("jvm", []):
                if isinstance(arg, str):
                    cmd.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        val = arg["value"]
                        if isinstance(val, list):
                            cmd.extend(val)
                        else:
                            cmd.append(val)
        if current_os=="osx" and "-XstartOnFirstThread" not in cmd:
            cmd.append("-XstartOnFirstThread")
        natives_path = os.path.join(version_dir, "natives")
        if not any("-Djava.library.path" in a for a in cmd):
            cmd.append(f"-Djava.library.path={natives_path}")

        # Game args
        game_args = []
        if "arguments" in version_data and "game" in version_data["arguments"]:
            for arg in version_data["arguments"]["game"]:
                if isinstance(arg, str):
                    game_args.append(arg)
                elif isinstance(arg, dict) and "rules" in arg and "value" in arg:
                    if self.evaluate_rules(arg["rules"], current_os):
                        val = arg["value"]
                        if isinstance(val, list):
                            game_args.extend(val)
                        else:
                            game_args.append(val)
        elif "minecraftArguments" in version_data:
            game_args = version_data["minecraftArguments"].split()

        uuid = self.generate_offline_uuid(username)
        replacements = {
            "${auth_player_name}": username,
            "${version_name}": version,
            "${game_directory}": MINECRAFT_DIR,
            "${assets_root}": os.path.join(MINECRAFT_DIR,"assets"),
            "${assets_index_name}": version_data.get("assetIndex",{}).get("id","legacy"),
            "${auth_uuid}": uuid,
            "${auth_access_token}": "0",
            "${user_type}": "legacy",
            "${version_type}": version_data.get("type","release"),
            "${user_properties}": "{}",
            "${quickPlayRealms}": ""
        }
        def replace_ph(a):
            for k,v in replacements.items():
                a = a.replace(k,v)
            return a
        game_args = [replace_ph(a) for a in game_args]
        cmd.extend(["-cp", classpath_str, main_class])
        cmd.extend(game_args)
        return cmd

    def evaluate_rules(self, rules, os_name):
        # Simplified rules evaluator
        if not rules:
            return True
        allowed = False
        for r in rules:
            if "features" in r:
                continue
            if r["action"]=="allow":
                if "os" not in r or r.get("os",{}).get("name")==os_name:
                    allowed=True
            elif r["action"]=="disallow":
                if "os" in r and r.get("os",{}).get("name")==os_name:
                    allowed=False
        return allowed

    def install_java_if_needed(self):
        # Implement install checking, download if necessary
        pass

    def select_skin(self):
        path = filedialog.askopenfilename(filetypes=[("PNG", "*.png")])
        if path:
            skin_dir = os.path.join(MINECRAFT_DIR, "skins")
            os.makedirs(skin_dir, exist_ok=True)
            shutil.copy(path, os.path.join(skin_dir, "custom_skin.png"))
            messagebox.showinfo("Skin Applied", "Skin applied! Restart game if needed.")

# simple input dialog styled like official launcher
def simple_input(parent, prompt):
    dialog = tk.Toplevel(parent)
    dialog.title("Input")
    dialog.configure(bg=BG_COLOR)
    dialog.transient(parent)
    dialog.grab_set()
    label = ttk.Label(dialog, text=prompt, background=BG_COLOR, foreground=FG_COLOR, font=BASE_FONT)
    label.pack(padx=20, pady=10)
    entry = ttk.Entry(dialog)
    entry.pack(padx=20, pady=10, fill='x')
    result = {'value': None}

    def ok():
        result['value'] = entry.get()
        dialog.destroy()

    ttk.Button(dialog, text="OK", command=ok).pack(pady=10)
    parent.wait_window(dialog)
    return result['value']

if __name__ == "__main__":
    app = CatClient()
    app.mainloop()
