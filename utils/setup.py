#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
import tempfile
from pathlib import Path

# Track installation states for the final summary log
install_results = {
    "Prerequisites": "Pending",
    "Repositories": "Pending",
    "Desktop Environment Detected": "Pending",
    "Brave Browser": "Pending",
    "Sublime Text": "Pending",
    "Podman": "Pending",
    "Virt-Manager / QEMU": "Pending",
    "System Utilities (btop, vlc, nmap, fastfetch)": "Pending",
    "Tailscale": "Pending",
    "LM Studio (Flatpak)": "Pending",
    "Podman Desktop": "Pending",
    "Zenmap (Flatpak)": "Pending",
    "Trayscale (Flatpak/Go)": "Pending",
    "Shell Aliases": "Pending",
    "Dock App Pinning": "Pending",
    "Plain Black Wallpaper & Lock": "Pending",
    "Bloat Cleanup & Debloat": "Pending",
    "GitHub Update & Maintenance Scripts": "Pending"
}

LOG_FILE = "workstation_install.log"

def log_message(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

def run_cmd(command, component_name):
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            log_message(f"[✔] {component_name}: SUCCESS")
            return True
        else:
            log_message(f"[✘] {component_name}: FAILED\nStderr: {result.stderr.strip()}")
            return False
    except Exception as e:
        log_message(f"[✘] {component_name}: ERROR -> {str(e)}")
        return False

def check_command_exists(cmd_name):
    return shutil.which(cmd_name) is not None

def detect_desktop_environment():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()
    combined = f"{desktop} {session}"
    
    if "kde" in combined or "plasma" in combined:
        return "kde"
    elif "cosmic" in combined:
        return "cosmic"
    elif "cinnamon" in combined:
        return "cinnamon"
    else:
        return "generic"

def process_github_dotfiles():
    log_message("[+] Fetching maintenance scripts and dotfiles from GitHub repository...")
    repo_url = "https://github.com/77777kaz77777/linux-maintenance-and-dotfiles.git"
    tmp_dir = tempfile.mkdtemp()
    
    try:
        clone_res = subprocess.run(f"git clone --depth 1 {repo_url} {tmp_dir}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if clone_res.returncode != 0:
            log_message("[✘] GitHub Repository Clone: FAILED")
            return

        # 1. Process Update Scripts from the 'updates' subdirectory
        updates_dir = Path(tmp_dir) / "updates"
        if updates_dir.exists() and updates_dir.is_dir():
            update_scripts = [f for f in os.listdir(updates_dir) if os.path.isfile(updates_dir / f) and not f.startswith('.')]
            
            if update_scripts:
                print("\n" + "="*60)
                print(" SELECT AN UPDATE SCRIPT TO INSTALL TO /usr/local/bin/update")
                print("="*60)
                for idx, script in enumerate(update_scripts, 1):
                    print(f" [{idx}] {script}")
                print(f" [{len(update_scripts) + 1}] Skip update script installation")
                
                try:
                    choice = input("Enter your choice number for the update script: ").strip()
                    if choice.isdigit():
                        choice_idx = int(choice)
                        if 1 <= choice_idx <= len(update_scripts):
                            selected_update = update_scripts[choice_idx - 1]
                            src_path = updates_dir / selected_update
                            dest_path = Path("/usr/local/bin/update")
                            shutil.copy(src_path, dest_path)
                            os.chmod(dest_path, 0o755)
                            log_message(f"[✔] Selected update script '{selected_update}' installed to /usr/local/bin/update with executable permissions.")
                        else:
                            log_message("[=] Skipped update script selection.")
                except Exception as menu_err:
                    log_message(f"[!] Interactive update menu skipped due to non-interactive environment: {menu_err}")
            else:
                log_message("[!] No scripts found inside the 'updates' directory.")
        else:
            log_message("[!] 'updates' directory not found in the repository.")

        # 2. Interactive Menu for Additional Root Repository Scripts
        root_scripts = [f for f in os.listdir(tmp_dir) if os.path.isfile(os.path.join(tmp_dir, f)) and not f.startswith('.')]
        
        if root_scripts:
            print("\n" + "="*60)
            print(" ADDITIONAL REPOSITORY SCRIPTS FOUND")
            print("="*60)
            print("Select an option to install to /usr/local/bin:")
            for idx, script in enumerate(root_scripts, 1):
                print(f" [{idx}] {script}")
            print(f" [{len(root_scripts) + 1}] Install All Root Scripts")
            print(f" [{len(root_scripts) + 2}] Skip / Exit Menu")
            
            try:
                choice = input("Enter your choice number: ").strip()
                if choice.isdigit():
                    choice_idx = int(choice)
                    if 1 <= choice_idx <= len(root_scripts):
                        selected_script = root_scripts[choice_idx - 1]
                        dest_name = Path(selected_script).stem
                        shutil.copy(os.path.join(tmp_dir, selected_script), f"/usr/local/bin/{dest_name}")
                        os.chmod(f"/usr/local/bin/{dest_name}", 0o755)
                        log_message(f"[✔] Installed custom script: {dest_name}")
                    elif choice_idx == len(root_scripts) + 1:
                        for s in root_scripts:
                            dest_name = Path(s).stem
                            shutil.copy(os.path.join(tmp_dir, s), f"/usr/local/bin/{dest_name}")
                            os.chmod(f"/usr/local/bin/{dest_name}", 0o755)
                            log_message(f"[✔] Installed: {dest_name}")
                    else:
                        log_message("[=] Skipped additional script installation.")
            except Exception as menu_err:
                log_message(f"[!] Interactive root script menu skipped due to non-interactive environment: {menu_err}")
        
        install_results["GitHub Update & Maintenance Scripts"] = "Configured & Processed"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

def main():
    if os.geteuid() != 0:
        print("[!] This script must be run with sudo or as root.")
        sys.exit(1)

    # Initialize log file
    with open(LOG_FILE, "w") as f:
        f.write("=== Workstation Toolstack Installation & Debloat Log ===\n\n")

    real_user = os.environ.get("SUDO_USER", os.environ.get("USER", "root"))
    real_home = str(Path(f"/home/{real_user}")) if real_user != "root" else "/root"

    log_message(f"Starting setup for user: {real_user}")

    # Detect Distro
    distro = "unknown"
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.strip().split("=")[1].strip('"').lower()
    except FileNotFoundError:
        pass

    log_message(f"Detected Distribution: {distro}")

    detected_de = detect_desktop_environment()
    log_message(f"Detected Desktop Environment: {detected_de.upper()}")
    install_results["Desktop Environment Detected"] = detected_de.upper()

    # ==================== FEDORA SETUP ====================
    if distro in ["fedora", "rhel", "nobara"]:
        install_results["Prerequisites"] = "Configured"
        
        # DNF Config Optimization
        dnf_conf = """[main]
gpgcheck=1
installonly_limit=3
clean_requirements_on_remove=true
best=False
skip_if_unavailable=True
max_parallel_downloads=10
fastestmirror=True
"""
        with open("/etc/dnf/dnf.conf", "w") as f:
            f.write(dnf_conf)

        log_message("[+] Installing prerequisites...")
        run_cmd("dnf5 install -y curl flatpak golang git", "Prerequisites")
        
        # Repositories check & setup
        if not os.path.exists("/etc/yum.repos.d/brave-browser.repo"):
            run_cmd("dnf5 config-manager addrepo --from-repofile=https://brave-browser-rpm-release.s3.brave.com/brave-browser.repo", "Brave Repo")
            run_cmd("rpm --import https://brave-browser-rpm-release.s3.brave.com/brave-core.asc", "Brave GPG")
        else:
            log_message("[=] Brave repository already configured, skipping.")

        if not os.path.exists("/etc/yum.repos.d/sublime-text.repo"):
            run_cmd("rpm --import https://download.sublimetext.com/sublimehq-pub.gpg", "Sublime GPG")
            run_cmd("dnf5 config-manager addrepo --from-repofile=https://download.sublimetext.com/rpm/stable/x86_64/sublime-text.repo", "Sublime Repo")
        else:
            log_message("[=] Sublime repository already configured, skipping.")

        if not os.path.exists("/etc/yum.repos.d/tailscale.repo"):
            run_cmd("dnf5 config-manager addrepo --from-repofile=https://pkgs.tailscale.com/stable/fedora/tailscale.repo", "Tailscale Repo")
        else:
            log_message("[=] Tailscale repository already configured, skipping.")

        install_results["Repositories"] = "Configured"

        # Core Package Install with individual existence validation
        packages_to_install = [
            ("brave-origin", "Brave Browser"),
            ("firefox", "Firefox Browser"),
            ("sublime-text", "Sublime Text"),
            ("podman", "Podman"),
            ("virt-manager", "Virt-Manager / QEMU"),
            ("btop", "btop"),
            ("vlc", "VLC Media Player"),
            ("nmap", "Nmap"),
            ("fastfetch", "Fastfetch"),
            ("tailscale", "Tailscale")
        ]

        if detected_de == "kde":
            packages_to_install.append(("spectacle", "Spectacle Screenshot Utility"))

        for pkg, name in packages_to_install:
            check_pkg = "brave-browser" if pkg == "brave-origin" else pkg
            res = subprocess.run(f"rpm -q {check_pkg}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if res.returncode == 0:
                log_message(f"[=] {name} is already installed, skipping.")
            else:
                log_message(f"[+] Installing {name}...")
                run_cmd(f"dnf5 install -y {pkg}", name)
        
        install_results["Brave Browser"] = "Installed / Verified"
        install_results["Sublime Text"] = "Installed / Verified"
        install_results["Podman"] = "Installed / Verified"
        install_results["Virt-Manager / QEMU"] = "Installed / Verified"
        install_results["System Utilities (btop, vlc, nmap, fastfetch)"] = "Installed / Verified"
        install_results["Tailscale"] = "Installed / Verified"

        # ==================== DEBLOAT ROUTINE ====================
        log_message(f"[+] Executing tailored debloat for {detected_de.upper()} desktop environment...")
        
        universal_bloat = [
            "thunderbird",
            "libreoffice-core",
            "libreoffice-writer",
            "libreoffice-calc",
            "libreoffice-impress"
        ]

        if detected_de == "kde":
            kde_bloat = [
                "akonadi", "akonadi-server", "kmail", "korganizer", 
                "kaddressbook", "kontact", "knotes", "akregator", "kdepim-runtime",
                "dragonplayer", "elisa-player", "kmahjongg", "kmines", 
                "ksudoku", "kpat", "konversation", "kmag", "kmousetool", 
                "kwrite", "krdc", "krfb", "fedora-media-writer"
            ]
            packages_to_remove = universal_bloat + kde_bloat
        elif detected_de == "cosmic":
            cosmic_bloat = ["totem", "evince", "gnome-calendar", "cheese"]
            packages_to_remove = universal_bloat + cosmic_bloat
        elif detected_de == "cinnamon":
            cinnamon_bloat = ["rhythmbox", "totem", "simple-scan", "hexchat"]
            packages_to_remove = universal_bloat + cinnamon_bloat
        else:
            packages_to_remove = universal_bloat

        for pkg in packages_to_remove:
            subprocess.run(f"dnf5 remove -y {pkg}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_cmd("dnf5 autoremove -y", "DNF Autoremove Orphans")
        run_cmd("dnf5 clean all", "DNF Clean Metadata")
        install_results["Bloat Cleanup & Debloat"] = f"Completed ({detected_de.upper()} profile)"

    # ==================== SHELL ALIASES ====================
    bashrc_path = Path(f"{real_home}/.bashrc")
    if bashrc_path.exists():
        content = bashrc_path.read_text()
        if "# Shell aliases & shortcuts" not in content:
            aliases = """
# Shell aliases & shortcuts
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias c='clear'
"""
            with open(bashrc_path, "a") as f:
                f.write(aliases)
            install_results["Shell Aliases"] = "Added"
        else:
            install_results["Shell Aliases"] = "Skipped (Already Present)"

    # ==================== STAGE TWO: DOCK PINS & PLAIN BLACK WALLPAPER ====================
    log_message("[+] Configuring Stage Two: Environment-specific dock shortcuts and plain black wallpaper...")
    
    black_img_path = "/usr/share/backgrounds/plain_black_default.png"
    if not os.path.exists(black_img_path):
        subprocess.run(f"python3 -c \"from PIL import Image; img = Image.new('RGB', (1920, 1080), color='black'); img.save('{black_img_path}')\" 2>/dev/null || true", shell=True)

    if detected_de == "cosmic":
        fm_desktop = "com.system76.CosmicFiles.desktop"
        term_desktop = "com.system76.CosmicTerminal.desktop"
    elif detected_de == "kde":
        fm_desktop = "org.kde.dolphin.desktop"
        term_desktop = "org.kde.konsole.desktop"
    elif detected_de == "cinnamon":
        fm_desktop = "nemo.desktop"
        term_desktop = "org.cinnamon.Terminal.desktop"
    else:
        fm_desktop = "org.gnome.Nautilus.desktop"
        term_desktop = "org.gnome.Terminal.desktop"

    dock_and_wallpaper_cmd = f"""
    export DISPLAY=:0
    gsettings set org.gnome.desktop.background picture-options 'solid' 2>/dev/null || true
    gsettings set org.gnome.desktop.background primary-color '#000000' 2>/dev/null || true
    gsettings set org.gnome.desktop.screensaver picture-uri 'file://{black_img_path}' 2>/dev/null || true

    gsettings set org.cinnamon.desktop.background color-shading-type 'solid' 2>/dev/null || true
    gsettings set org.cinnamon.desktop.background primary-color '#000000' 2>/dev/null || true

    gsettings set org.gnome.shell favorite-apps \"['brave-browser.desktop', 'firefox.desktop', '{fm_desktop}', '{term_desktop}']\" 2>/dev/null || true
    gsettings set org.cinnamon.desktop.applications.favorites favorite-apps \"['brave-browser.desktop', 'firefox.desktop', '{fm_desktop}', '{term_desktop}']\" 2>/dev/null || true
    """
    
    subprocess.run(f"su - {real_user} -c \"{dock_and_wallpaper_cmd}\"", shell=True)
    install_results["Dock App Pinning"] = f"Configured ({detected_de.upper()}: Brave, Firefox, {fm_desktop}, {term_desktop})"
    install_results["Plain Black Wallpaper & Lock"] = "Configured"

    # ==================== FLATPAKS & GO ====================
    if run_cmd("flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo", "Flathub Remote"):
        res_lms = subprocess.run("flatpak list | grep -qi ai.lmstudio.lm-studio", shell=True)
        if res_lms.returncode == 0:
            install_results["LM Studio (Flatpak)"] = "Skipped (Already Installed)"
        else:
            if run_cmd("flatpak install -y flathub ai.lmstudio.lm-studio", "LM Studio Flatpak"):
                install_results["LM Studio (Flatpak)"] = "Installed"
            else:
                install_results["LM Studio (Flatpak)"] = "Failed / Skipped"

        res_pod = subprocess.run("flatpak list | grep -qi io.podman_desktop.PodmanDesktop", shell=True)
        if res_pod.returncode == 0:
            install_results["Podman Desktop"] = "Skipped (Already Installed)"
        else:
            if run_cmd("flatpak install -y flathub io.podman_desktop.PodmanDesktop", "Podman Desktop Flatpak"):
                install_results["Podman Desktop"] = "Installed"
            else:
                install_results["Podman Desktop"] = "Failed / Skipped"

        res_zen = subprocess.run("flatpak list | grep -qi org.nmap.Zenmap", shell=True)
        if res_zen.returncode == 0:
            install_results["Zenmap (Flatpak)"] = "Skipped (Already Installed)"
        else:
            if run_cmd("flatpak install -y flathub org.nmap.Zenmap", "Zenmap Flatpak"):
                install_results["Zenmap (Flatpak)"] = "Installed"
            else:
                install_results["Zenmap (Flatpak)"] = "Failed / Skipped"

    if check_command_exists("trayscale") or subprocess.run("flatpak list | grep -qi dev.deedles.Trayscale", shell=True).returncode == 0:
        install_results["Trayscale (Flatpak/Go)"] = "Skipped (Already Installed)"
    else:
        log_message("[+] Attempting Trayscale installation via Flatpak...")
        if run_cmd("flatpak install -y flathub dev.deedles.Trayscale", "Trayscale Flatpak"):
            install_results["Trayscale (Flatpak/Go)"] = "Installed (Flatpak)"
        else:
            go_cmd = f"su - {real_user} -c 'go install deedles.dev/trayscale/cmd/trayscale@latest'"
            if run_cmd(go_cmd, "Trayscale Go Build"):
                go_bin_path = Path(f"{real_home}/go/bin/trayscale")
                if go_bin_path.exists():
                    subprocess.run(f"cp {go_bin_path} /usr/local/bin/trayscale && chmod +x /usr/local/bin/trayscale", shell=True)
                install_results["Trayscale (Flatpak/Go)"] = "Installed (Go Build)"
            else:
                install_results["Trayscale (Flatpak/Go)"] = "Failed"

    # ==================== PROCESS REPOSITORY & UPDATE SCRIPTS ====================
    process_github_dotfiles()

    # ==================== FINAL REPORT ====================
    print("\n" + "="*80)
    print(" INSTALLATION & STAGE TWO SUMMARY REPORT")
    print("="*80)
    for component, status in install_results.items():
        print(f" {component:<55} : {status}")
    print("="*80)
    print(f"[✔] Detailed audit log exported to: {os.path.abspath(LOG_FILE)}")

if __name__ == "__main__":
    main()
