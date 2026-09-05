#!/usr/bin/env python3
# (Work in Progress) Automated Python workstation bootstrap, toolstack installer, and repository script deployment with GUI.
import os
import sys
import subprocess
import shutil
import tempfile
import threading
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path

LOG_FILE = "workstation_install.log"

class SystemManager:
    """Abstracts package management and OS-level operations across different distributions."""
    def __init__(self):
        self.os_version = "9" 
        self.os_codename = "bullseye" 
        self.distro = self._detect_distro()
        self.de = self._detect_desktop_environment()
        self.pkg_mgr, self.install_cmd, self.remove_cmd, self.update_cmd = self._detect_package_manager()
        self.real_user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))
        self.real_home = os.path.expanduser(f"~{self.real_user}")

    def _detect_distro(self):
        distro = "unknown"
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.strip().split("=")[1].strip('"').lower()
                    elif line.startswith("VERSION_ID="):
                        self.os_version = line.strip().split("=")[1].strip('"').split('.')[0]
                    elif line.startswith("VERSION_CODENAME="):
                        self.os_codename = line.strip().split("=")[1].strip('"').lower()
        except FileNotFoundError:
            pass
        return distro

    def _detect_desktop_environment(self):
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        session = os.environ.get("DESKTOP_SESSION", "").lower()
        combined = f"{desktop} {session}"
        
        if "kde" in combined or "plasma" in combined:
            return "kde"
        elif "gnome" in combined:
            return "gnome"
        elif "cosmic" in combined:
            return "cosmic"
        elif "cinnamon" in combined:
            return "cinnamon"
        else:
            return "generic"

    def _detect_package_manager(self):
        if shutil.which("dnf5"):
            return "dnf5", "dnf5 install -y", "dnf5 remove -y", "dnf5 update -y"
        elif shutil.which("dnf"):
            return "dnf4", "dnf install -y", "dnf remove -y", "dnf update -y"
        elif shutil.which("apt-get"):
            return "apt", "DEBIAN_FRONTEND=noninteractive apt-get install -y", "DEBIAN_FRONTEND=noninteractive apt-get remove -y", "apt-get update -y"
        elif shutil.which("pacman"):
            return "pacman", "pacman -S --noconfirm", "pacman -Rns --noconfirm", "pacman -Sy"
        elif shutil.which("zypper"):
            return "zypper", "zypper in -y", "zypper rm -y", "zypper ref"
        else:
            return None, None, None, None

    def configure_repositories(self, logger):
        if self.pkg_mgr in ["dnf4", "dnf5"]:
            if self.distro in ['centos', 'rocky', 'almalinux']:
                ts_repo = f"https://pkgs.tailscale.com/stable/centos/{self.os_version}/tailscale.repo"
            elif self.distro == 'rhel':
                ts_repo = f"https://pkgs.tailscale.com/stable/rhel/{self.os_version}/tailscale.repo"
            else:
                ts_repo = "https://pkgs.tailscale.com/stable/fedora/tailscale.repo"

            if self.pkg_mgr == "dnf5":
                if not os.path.exists("/etc/yum.repos.d/brave-browser.repo"):
                    subprocess.run("dnf5 config-manager addrepo --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo", shell=True)
                    subprocess.run("rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc", shell=True)
                if not os.path.exists("/etc/yum.repos.d/sublime-text.repo"):
                    subprocess.run("rpm --import https://download.sublimetext.com/sublimehq-pub.gpg", shell=True)
                    subprocess.run("dnf5 config-manager addrepo --from-repofile=https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo", shell=True)
                if not os.path.exists("/etc/yum.repos.d/tailscale.repo"):
                    subprocess.run(f"dnf5 config-manager addrepo --from-repofile={ts_repo}", shell=True)
                logger("Configured DNF5 repositories for Brave, Sublime, and Tailscale.")

            elif self.pkg_mgr == "dnf4":
                subprocess.run("dnf install -y dnf-plugins-core", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if not os.path.exists("/etc/yum.repos.d/brave-browser.repo"):
                    subprocess.run("dnf config-manager --add-repo https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo", shell=True)
                    subprocess.run("rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc", shell=True)
                if not os.path.exists("/etc/yum.repos.d/sublime-text.repo"):
                    subprocess.run("rpm --import https://download.sublimetext.com/sublimehq-pub.gpg", shell=True)
                    subprocess.run("dnf config-manager --add-repo https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo", shell=True)
                if not os.path.exists("/etc/yum.repos.d/tailscale.repo"):
                    subprocess.run(f"dnf config-manager --add-repo {ts_repo}", shell=True)
                logger("Configured DNF4 repositories for Brave, Sublime, and Tailscale.")

        elif self.pkg_mgr == "apt":
            logger("Configuring APT repositories...")
            subprocess.run("curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg", shell=True)
            subprocess.run('echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg] https://brave-browser-apt-release.s3.brave.com/ stable main" > /etc/apt/sources.list.d/brave-browser-release.list', shell=True)
            
            subprocess.run("wget -qO - https://download.sublimetext.com/sublimehq-pub.gpg | gpg --dearmor -o /usr/share/keyrings/sublimehq-archive-keyring.gpg", shell=True)
            subprocess.run('echo "deb [signed-by=/usr/share/keyrings/sublimehq-archive-keyring.gpg] https://download.sublimetext.com/ apt/stable/" > /etc/apt/sources.list.d/sublime-text.list', shell=True)
            
            os_id = "ubuntu" if "ubuntu" in self.distro else "debian"
            ts_apt_url = f"https://pkgs.tailscale.com/stable/{os_id} {self.os_codename} main"
            subprocess.run("curl -fsSL https://pkgs.tailscale.com/stable/debian/bullseye.noarmor.gpg | tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null", shell=True)
            subprocess.run(f'echo "deb [signed-by=/usr/share/keyrings/tailscale-archive-keyring.gpg] {ts_apt_url}" > /etc/apt/sources.list.d/tailscale.list', shell=True)
            subprocess.run(self.update_cmd, shell=True)
        else:
            logger(f"Repository auto-config is not supported for {self.pkg_mgr}. Will attempt standard repository installations or skip specific packages.")


class InstallerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Linux Workstation Bootstrap Installer")
        self.geometry("850x700")
        self.configure(padx=10, pady=10)
        self.sys_mgr = SystemManager()
        self.log_queue = queue.Queue()
        self.install_thread = None
        
        self.choice_event = threading.Event()
        self.user_choice = None

        if os.geteuid() != 0:
            messagebox.showerror("Privilege Error", "This script must be run as root (sudo). Please relaunch with elevated privileges.")
            self.destroy()
            sys.exit(1)

        self._build_ui()
        self.after(100, self._process_log_queue)

    def _build_ui(self):
        header_frame = ttk.LabelFrame(self, text="System Information")
        header_frame.pack(fill="x", pady=5)
        
        info_text = f"Distro: {self.sys_mgr.distro.upper()}  |  Desktop: {self.sys_mgr.de.upper()}  |  Target User: {self.sys_mgr.real_user}  |  Package Manager: {self.sys_mgr.pkg_mgr}"
        ttk.Label(header_frame, text=info_text, font=("Helvetica", 10, "bold")).pack(pady=5)

        options_frame = ttk.LabelFrame(self, text="Installation Options")
        options_frame.pack(fill="x", pady=5)

        self.opt_prereqs = tk.BooleanVar(value=True)
        self.opt_core = tk.BooleanVar(value=True)
        self.opt_debloat = tk.BooleanVar(value=True)
        self.opt_flatpaks = tk.BooleanVar(value=True)
        self.opt_github = tk.BooleanVar(value=True)
        self.opt_term = tk.BooleanVar(value=True)

        ttk.Checkbutton(options_frame, text="Install Prerequisites & Repositories", variable=self.opt_prereqs).grid(row=0, column=0, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Install Core Toolstack (Brave, Sublime, Podman, Virt-Manager, Tailscale, Alacritty)", variable=self.opt_core).grid(row=1, column=0, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Execute Distro/DE Debloat Routine", variable=self.opt_debloat).grid(row=2, column=0, sticky="w", padx=10, pady=2)
        
        ttk.Checkbutton(options_frame, text="Install Flatpaks (LM Studio, Podman Desktop, Zenmap)", variable=self.opt_flatpaks).grid(row=0, column=1, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Clone & Install GitHub Maintenance Scripts", variable=self.opt_github).grid(row=1, column=1, sticky="w", padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Configure Shell Aliases & Terminal Theme", variable=self.opt_term).grid(row=2, column=1, sticky="w", padx=10, pady=2)

        log_frame = ttk.LabelFrame(self, text="Execution Log")
        log_frame.pack(fill="both", expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="black", fg="lightgreen", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=5)
        self.btn_start = ttk.Button(btn_frame, text="Start Installation", command=self.start_installation)
        self.btn_start.pack(side="left", padx=5)
        self.btn_exit = ttk.Button(btn_frame, text="Exit", command=self.destroy)
        self.btn_exit.pack(side="right", padx=5)

    def log(self, message):
        self.log_queue.put(message)
        with open(LOG_FILE, "a") as f:
            f.write(message + "\n")

    def _process_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        self.after(100, self._process_log_queue)

    def show_script_selector(self, scripts, title, is_update_dir):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry("450x300")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Select a script to install:", font=("Helvetica", 10, "bold")).pack(pady=10)
        
        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE, font=("Consolas", 10))
        listbox.pack(fill="both", expand=True, padx=15, pady=5)
        
        for script in scripts:
            listbox.insert(tk.END, script)
            
        def on_select():
            sel = listbox.curselection()
            if sel:
                self.user_choice = ("SELECT", scripts[sel[0]])
            else:
                self.user_choice = ("SKIP", None)
            dialog.destroy()
            self.choice_event.set()
            
        def on_all():
            self.user_choice = ("ALL", None)
            dialog.destroy()
            self.choice_event.set()
            
        def on_skip():
            self.user_choice = ("SKIP", None)
            dialog.destroy()
            self.choice_event.set()

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="Install Selected", command=on_select).pack(side="left", padx=5)
        if not is_update_dir:
            ttk.Button(btn_frame, text="Install All", command=on_all).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Skip", command=on_skip).pack(side="left", padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", on_skip)

    def run_cmd(self, command, component_name):
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                self.log(f"[✔] {component_name}: SUCCESS")
                return True
            else:
                self.log(f"[✘] {component_name}: FAILED\n    Stderr: {result.stderr.strip()}")
                return False
        except Exception as e:
            self.log(f"[✘] {component_name}: ERROR -> {str(e)}")
            return False

    def start_installation(self):
        if not self.sys_mgr.pkg_mgr:
            messagebox.showerror("Error", "Unsupported package manager. Unable to proceed.")
            return

        self.btn_start.config(state=tk.DISABLED)
        open(LOG_FILE, "w").write("=== GUI Workstation Installation Log ===\n\n")
        self.install_thread = threading.Thread(target=self._installation_process, daemon=True)
        self.install_thread.start()

    def _installation_process(self):
        self.log("--- Starting Installation Sequence ---")

        if self.opt_prereqs.get():
            self.log("[+] Installing system prerequisites...")
            pkgs = "curl flatpak golang git wget unzip"
            self.run_cmd(f"{self.sys_mgr.install_cmd} {pkgs}", "Core Prerequisites")
            
            # Apply DNF Optimizations if applicable
            if self.sys_mgr.pkg_mgr in ["dnf4", "dnf5"]:
                dnf_conf_content = r"""[main]
gpgcheck=1
installonly_limit=3
clean_requirements_on_remove=true
best=False
skip_if_unavailable=True
max_parallel_downloads=10
fastestmirror=True
"""
                try:
                    with open("/etc/dnf/dnf.conf", "w") as f:
                        f.write(dnf_conf_content)
                    self.log("[✔] Applied optimized DNF configuration.")
                except Exception as e:
                    self.log(f"[✘] Failed to apply DNF config: {e}")

            self.sys_mgr.configure_repositories(self.log)

        if self.opt_core.get():
            self.log("[+] Installing core toolstack...")
            brave_pkg = "brave-browser" if self.sys_mgr.pkg_mgr == "apt" else "brave-origin"
            packages = [brave_pkg, "firefox", "sublime-text", "podman", "virt-manager", "btop", "vlc", "nmap", "fastfetch", "tailscale", "alacritty"]
            
            if self.sys_mgr.de == "kde":
                spectacle = "spectacle" if self.sys_mgr.pkg_mgr != "apt" else "kde-spectacle"
                packages.append(spectacle)

            for pkg in packages:
                self.run_cmd(f"{self.sys_mgr.install_cmd} {pkg}", pkg.title())

        if self.opt_debloat.get():
            self.log(f"[+] Executing tailored debloat for {self.sys_mgr.de.upper()} on {self.sys_mgr.distro}...")
            universal_bloat = ["thunderbird", "libreoffice-core", "libreoffice-writer", "libreoffice-calc", "libreoffice-impress"]
            kde_bloat = ["akonadi", "kmail", "dragonplayer", "kmines", "fedora-media-writer"]
            gnome_bloat = ["gnome-tour", "epiphany-browser", "gnome-weather", "gnome-clocks", "gnome-maps", "totem", "cheese"]
            cosmic_bloat = ["totem", "evince", "gnome-calendar", "cheese"]
            cinnamon_bloat = ["rhythmbox", "totem", "hexchat"]
            apt_bloat = ["snapd", "gnome-software-plugin-snap"]

            remove_list = universal_bloat
            if self.sys_mgr.de == "kde": remove_list += kde_bloat
            if self.sys_mgr.de == "gnome": remove_list += gnome_bloat
            if self.sys_mgr.de == "cosmic": remove_list += cosmic_bloat
            if self.sys_mgr.de == "cinnamon": remove_list += cinnamon_bloat
            if self.sys_mgr.pkg_mgr == "apt": remove_list += apt_bloat

            for pkg in remove_list:
                subprocess.run(f"{self.sys_mgr.remove_cmd} {pkg}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if self.sys_mgr.pkg_mgr in ["dnf4", "dnf5"]:
                base_cmd = "dnf5" if self.sys_mgr.pkg_mgr == "dnf5" else "dnf"
                self.run_cmd(f"{base_cmd} autoremove -y && {base_cmd} clean all", "DNF Cleanup")
            elif self.sys_mgr.pkg_mgr == "apt":
                self.run_cmd("apt-get autoremove -y && apt-get clean", "APT Cleanup")
            elif self.sys_mgr.pkg_mgr == "pacman":
                self.run_cmd("pacman -Sc --noconfirm", "Pacman Cleanup")

        if self.opt_flatpaks.get():
            self.log("[+] Installing Flatpaks & Trayscale...")
            if shutil.which("flatpak"):
                self.run_cmd("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo", "Flathub Remote")
                self.run_cmd("flatpak install -y flathub ai.lmstudio.lm-studio", "LM Studio")
                self.run_cmd("flatpak install -y flathub io.podman_desktop.PodmanDesktop", "Podman Desktop")
                self.run_cmd("flatpak install -y flathub org.nmap.Zenmap", "Zenmap")
                
                if not shutil.which("trayscale") and subprocess.run("flatpak list | grep -qi dev.deedles.Trayscale", shell=True).returncode != 0:
                    if not self.run_cmd("flatpak install -y flathub dev.deedles.Trayscale", "Trayscale (Flatpak)"):
                        if shutil.which("go"):
                            go_cmd = f"su - {self.sys_mgr.real_user} -c 'go install deedles.dev/trayscale/cmd/trayscale@latest'"
                            if self.run_cmd(go_cmd, "Trayscale (Go Build)"):
                                go_bin = Path(f"{self.sys_mgr.real_home}/go/bin/trayscale")
                                if go_bin.exists():
                                    subprocess.run(f"cp {go_bin} /usr/local/bin/trayscale && chmod +x /usr/local/bin/trayscale", shell=True)
                        else:
                            self.log("[!] Go compiler not found. Trayscale build skipped.")
            else:
                self.log("[!] Flatpak is not installed. Skipping Flatpak installations.")

        if self.opt_github.get():
            self.log("[+] Deploying GitHub maintenance scripts...")
            if shutil.which("git"):
                repo_url = "https://github.com/77777kaz77777/linux-maintenance-and-dotfiles.git"
                tmp_dir = tempfile.mkdtemp()
                if self.run_cmd(f"git clone --depth 1 {repo_url} {tmp_dir}", "GitHub Clone"):
                    
                    updates_dir = Path(tmp_dir) / "updates"
                    if updates_dir.exists():
                        update_scripts = [f for f in os.listdir(updates_dir) if os.path.isfile(updates_dir / f) and not f.startswith('.')]
                        if update_scripts:
                            self.choice_event.clear()
                            self.user_choice = None
                            self.after(0, self.show_script_selector, update_scripts, "Select Update Script", True)
                            self.choice_event.wait()
                            
                            if self.user_choice and self.user_choice[0] == "SELECT":
                                selected = self.user_choice[1]
                                src = updates_dir / selected
                                dest = "/usr/local/bin/update"
                                shutil.copy(src, dest)
                                os.chmod(dest, 0o755)
                                self.log(f"[✔] Installed update script '{selected}' to {dest}")
                            else:
                                self.log("[=] Skipped update script installation.")

                    root_scripts = [f for f in os.listdir(tmp_dir) if os.path.isfile(Path(tmp_dir) / f) and not f.startswith('.')]
                    if root_scripts:
                        self.choice_event.clear()
                        self.user_choice = None
                        self.after(0, self.show_script_selector, root_scripts, "Select Additional Tool Scripts", False)
                        self.choice_event.wait()
                        
                        if self.user_choice and self.user_choice[0] == "SELECT":
                            selected = self.user_choice[1]
                            src = Path(tmp_dir) / selected
                            dest = f"/usr/local/bin/{Path(selected).stem}"
                            shutil.copy(src, dest)
                            os.chmod(dest, 0o755)
                            self.log(f"[✔] Installed tool script '{selected}' to {dest}")
                        elif self.user_choice and self.user_choice[0] == "ALL":
                            for script in root_scripts:
                                src = Path(tmp_dir) / script
                                dest = f"/usr/local/bin/{Path(script).stem}"
                                shutil.copy(src, dest)
                                os.chmod(dest, 0o755)
                                self.log(f"[✔] Installed tool script '{script}' to {dest}")
                        else:
                            self.log("[=] Skipped additional root scripts.")
                            
                shutil.rmtree(tmp_dir, ignore_errors=True)
            else:
                self.log("[!] Git is not installed. Skipping GitHub deployment.")

        if self.opt_term.get():
            self.log("[+] Configuring Shell Aliases, Konsole, and Alacritty Themes...")
            
            # 1. Shell Aliases logic
            bashrc_path = Path(self.sys_mgr.real_home) / ".bashrc"
            try:
                if bashrc_path.exists():
                    content = bashrc_path.read_text()
                    if "# Shell aliases & shortcuts" not in content:
                        aliases_block = r"""
# Shell aliases & shortcuts

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# some more ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias c='clear'
"""
                        with open(bashrc_path, "a") as f:
                            f.write("\n" + aliases_block)
                        self.log("[✔] Shell aliases appended to .bashrc")
                    else:
                        self.log("[=] Shell aliases already present in .bashrc")
            except Exception as e:
                self.log(f"[✘] Failed to update .bashrc with aliases: {e}")

            # 2. Konsole theme logic
            konsole_script_content = r"""#!/bin/bash
# Sets terminal background to solid black (#000000), default text to pure white
set -euo pipefail

apply_runtime_colors() {
    printf '\033]10;#FFFFFF\007'
    printf '\033]11;#000000\007'
    export PS1='\u@\h:\w\$ '
    clear
}

apply_persistent_scheme() {
    local scheme_dir="${HOME}/.local/share/konsole"
    local scheme_file="${scheme_dir}/PureWhiteOnBlack.colorscheme"
    mkdir -p "${scheme_dir}"

    cat << 'EOF' > "${scheme_file}"
[General]
Description=Pure White on Black
Opacity=1

[Background]
Color=0,0,0
[BackgroundFaint]
Color=0,0,0
[BackgroundIntense]
Color=0,0,0
[Foreground]
Color=255,255,255
[ForegroundFaint]
Color=200,200,200
[ForegroundIntense]
Color=255,255,255
[Color0]
Color=0,0,0
[Color0Intense]
Color=128,128,128
[Color7]
Color=220,220,220
[Color7Intense]
Color=255,255,255
EOF
    local default_profile="${scheme_dir}/Profile 1.profile"
    if [[ -f "${default_profile}" ]]; then
        if grep -q "^ColorScheme=" "${default_profile}"; then
            sed -i 's/^ColorScheme=.*/ColorScheme=PureWhiteOnBlack/' "${default_profile}"
        else
            echo "ColorScheme=PureWhiteOnBlack" >> "${default_profile}"
        fi
    fi
}

update_bashrc_prompt() {
    local bashrc="${HOME}/.bashrc"
    local prompt_entry='export PS1="\u@\h:\w\$ "'
    if [[ -f "${bashrc}" ]]; then
        if ! grep -qF 'export PS1="\u@\h:\w\$ "' "${bashrc}"; then
            echo "" >> "${bashrc}"
            echo "# Override shell prompt to use default white text" >> "${bashrc}"
            echo "${prompt_entry}" >> "${bashrc}"
        fi
    fi
}

main() {
    apply_runtime_colors
    apply_persistent_scheme
    update_bashrc_prompt
}
main "$@"
"""
            konsole_sh_path = "/tmp/setup_konsole.sh"
            try:
                with open(konsole_sh_path, "w") as f:
                    f.write(konsole_script_content)
                os.chmod(konsole_sh_path, 0o755)
                self.run_cmd(f"su - {self.sys_mgr.real_user} -c 'bash {konsole_sh_path}'", "Konsole Color Scheme & Bash Prompt")
            except Exception as e:
                self.log(f"[✘] Failed to setup Konsole configuration: {e}")
            finally:
                if os.path.exists(konsole_sh_path):
                    os.remove(konsole_sh_path)

            # 3. Alacritty Font and Theme Logic
            alacritty_script_content = r"""#!/bin/bash
set -euo pipefail

# Download and install JetBrains Mono Nerd Font
curl -LO https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip
mkdir -p ~/.local/share/fonts/JetBrainsMono
unzip -q -o JetBrainsMono.zip -d ~/.local/share/fonts/JetBrainsMono
fc-cache -fv
rm JetBrainsMono.zip

# Create Alacritty Configuration
mkdir -p ~/.config/alacritty
cat << 'EOF' > ~/.config/alacritty/alacritty.toml
[general]
live_config_reload = true

[env]
TERM = "xterm-256color"

[window]
padding = { x = 12, y = 12 }
decorations = "Full"
opacity = 1.0
blur = true
startup_mode = "Windowed"
dynamic_title = true

[font]
size = 17.0

[font.normal]
family = "JetBrainsMono Nerd Font"
style = "Regular"

[font.bold]
family = "JetBrainsMono Nerd Font"
style = "Bold"

[font.italic]
family = "JetBrainsMono Nerd Font"
style = "Italic"

[font.bold_italic]
family = "JetBrainsMono Nerd Font"
style = "Bold Italic"

[scrolling]
history = 10000
multiplier = 3

[cursor]
style = { shape = "Block", blinking = "On" }
blink_interval = 750
unfocused_hollow = true

[selection]
save_to_clipboard = true

[colors.primary]
background = "#121212"
foreground = "#e0e0e0"

[colors.selection]
text = "CellForeground"
background = "#282828"

[colors.normal]
black   = "#161616"
red     = "#c30010"
green   = "#90a959"
yellow  = "#f4bf75"
blue    = "#6a9fb5"
magenta = "#aa759f"
cyan    = "#75b5aa"
white   = "#e0e0e0"

[colors.bright]
black   = "#404040"
red     = "#e55555"
green   = "#aac474"
yellow  = "#feca88"
blue    = "#82b8c8"
magenta = "#c28cb8"
cyan    = "#93d3c3"
white   = "#ffffff"

[[keyboard.bindings]]
key = "V"
mods = "Control"
action = "Paste"

[[keyboard.bindings]]
key = "C"
mods = "Control"
action = "Copy"

[[keyboard.bindings]]
key = "0"
mods = "Control"
action = "ResetFontSize"

[[keyboard.bindings]]
key = "="
mods = "Control"
action = "IncreaseFontSize"

[[keyboard.bindings]]
key = "-"
mods = "Control"
action = "DecreaseFontSize"

[[keyboard.bindings]]
key = "Enter"
mods = "Control|Shift"
action = "SpawnNewInstance"
EOF
"""
            alacritty_sh_path = "/tmp/setup_alacritty.sh"
            try:
                with open(alacritty_sh_path, "w") as f:
                    f.write(alacritty_script_content)
                os.chmod(alacritty_sh_path, 0o755)
                self.run_cmd(f"su - {self.sys_mgr.real_user} -c 'bash {alacritty_sh_path}'", "Alacritty Setup & Fonts")
            except Exception as e:
                self.log(f"[✘] Failed to setup Alacritty: {e}")
            finally:
                if os.path.exists(alacritty_sh_path):
                    os.remove(alacritty_sh_path)

        self.log("--- Installation Sequence Complete ---")
        self.btn_start.config(state=tk.NORMAL)
        messagebox.showinfo("Complete", f"Deployment finished. Log saved to {os.path.abspath(LOG_FILE)}")

if __name__ == "__main__":
    app = InstallerGUI()
    app.mainloop()
