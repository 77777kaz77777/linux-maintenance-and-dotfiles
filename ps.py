import os
import csv
import socket
import logging
import ipaddress
import concurrent.futures
from datetime import datetime
from pathlib import Path

import nmap

# ============================================================
# Configuration
# ============================================================

COMMON_PORTS = [
    20,21,22,23,25,
    53,
    80,
    110,
    123,
    143,
    161,
    389,
    443,
    445,
    587,
    993,
    995,
    1433,
    1521,
    3306,
    3389,
    5432,
    5900,
    6379,
    8080
]

SECURITY_PORTS = {
    23: "Telnet",
    21: "FTP",
    69: "TFTP"
}

RESERVED_PORTS = set(range(1,1024))

DEFAULT_TIMEOUT = 1

DEFAULT_THREADS = 100

DOWNLOAD_FOLDER = Path.home() / "Downloads"

# ============================================================
# Colours
# ============================================================

class Colour:

    RED="\033[91m"
    GREEN="\033[92m"
    YELLOW="\033[93m"
    CYAN="\033[96m"
    BLUE="\033[94m"
    RESET="\033[0m"

# ============================================================
# Logger
# ============================================================

def configure_logger(target):

    log_file = DOWNLOAD_FOLDER / \
        f"{target}_{datetime.now():%Y%m%d_%H%M%S}_scan.log"

    logger=logging.getLogger()

    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter=logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )

    fh=logging.FileHandler(log_file)

    fh.setFormatter(formatter)

    sh=logging.StreamHandler()

    sh.setFormatter(formatter)

    logger.addHandler(fh)

    logger.addHandler(sh)

    return logger

# ============================================================
# Banner
# ============================================================

def print_banner():

    print()

    print("="*60)

    print("        PROFESSIONAL PYTHON PORT SCANNER")

    print("="*60)

# ============================================================
# Validation
# ============================================================

def validate_ip(target):

    try:

        ipaddress.ip_address(target)

        return True

    except ValueError:

        return False


def validate_hostname(host):

    try:

        socket.gethostbyname(host)

        return True

    except socket.error:

        return False


def validate_target(target):

    return validate_ip(target) or validate_hostname(target)


def validate_port(port):

    try:

        port=int(port)

        if 1<=port<=65535:

            return port

    except ValueError:

        pass

    return None

# ============================================================
# User Input
# ============================================================

def get_targets():

    while True:

        raw=input(
            "\nEnter IP address(es) or hostname(s): "
        ).split()

        valid=[]
        invalid=[]

        for item in raw:

            if validate_target(item):

                valid.append(item)

            else:

                invalid.append(item)

        if invalid:

            print()

            print(
                Colour.RED+
                "Invalid target(s): "+
                ", ".join(invalid)+
                Colour.RESET
            )

        else:

            return valid


def get_timeout():

    value=input(
        f"Socket timeout [{DEFAULT_TIMEOUT}s]: "
    ).strip()

    if value=="":

        return DEFAULT_TIMEOUT

    try:

        return float(value)

    except ValueError:

        return DEFAULT_TIMEOUT


def get_workers():

    value=input(
        f"Worker threads [{DEFAULT_THREADS}]: "
    ).strip()

    if value=="":

        return DEFAULT_THREADS

    try:

        return max(1,int(value))

    except ValueError:

        return DEFAULT_THREADS

        # ============================================================
# Progress Display
# ============================================================

def print_progress(current, total):

    percent = (current / total) * 100

    bar_length = 40

    filled = int(bar_length * current / total)

    bar = "█" * filled + "-" * (bar_length - filled)

    print(
        f"\r[{bar}] {current}/{total} ({percent:.1f}%)",
        end="",
        flush=True
    )

# ============================================================
# Single Port Scan
# ============================================================

def scan_port(
    target,
    port,
    timeout,
    allow_reserved_ports
):

    if port in RESERVED_PORTS and not allow_reserved_ports:

        return port, "Skipped (Reserved Port)"

    try:

        with socket.create_connection(
            (target, port),
            timeout=timeout
        ):

            if port in SECURITY_PORTS:

                return (
                    port,
                    f"Open (Security Risk - {SECURITY_PORTS[port]})"
                )

            return port, "Open"

    except ConnectionRefusedError:

        return port, "Closed"

    except socket.timeout:

        return port, "Filtered"

    except OSError:

        return port, "Host Unreachable"

    except Exception as e:

        return port, f"Error ({e})"

# ============================================================
# Thread Worker
# ============================================================

def scan_worker(args):

    return scan_port(*args)

# ============================================================
# Sequential Scan
# ============================================================

def sequential_scan(
    target,
    ports,
    timeout,
    allow_reserved_ports
):

    results = []

    total = len(ports)

    for index, port in enumerate(ports, start=1):

        results.append(

            scan_port(
                target,
                port,
                timeout,
                allow_reserved_ports
            )

        )

        print_progress(index, total)

    print()

    return results

# ============================================================
# Multithreaded Scan
# ============================================================

def threaded_scan(
    target,
    ports,
    timeout,
    allow_reserved_ports,
    workers
):

    args = [

        (
            target,
            port,
            timeout,
            allow_reserved_ports
        )

        for port in ports

    ]

    results = []

    total = len(args)

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        futures = {

            executor.submit(scan_worker, item): item

            for item in args

        }

        completed = 0

        for future in concurrent.futures.as_completed(futures):

            completed += 1

            results.append(future.result())

            print_progress(completed, total)

    print()

    results.sort(key=lambda x: x[0])

    return results

# ============================================================
# Multiprocessing Scan
# ============================================================

def process_scan(
    target,
    ports,
    timeout,
    allow_reserved_ports,
    workers
):

    args = [

        (
            target,
            port,
            timeout,
            allow_reserved_ports
        )

        for port in ports

    ]

    total = len(args)

    results = []

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers
    ) as executor:

        completed = 0

        for result in executor.map(scan_worker, args):

            completed += 1

            results.append(result)

            print_progress(completed, total)

    print()

    results.sort(key=lambda x: x[0])

    return results

# ============================================================
# Scan Dispatcher
# ============================================================

def run_scan(

    target,

    ports,

    timeout,

    allow_reserved_ports,

    workers,

    mode

):

    start = datetime.now()

    if mode == "t":

        print(
            Colour.CYAN +
            "\nStarting multithreaded scan...\n" +
            Colour.RESET
        )

        results = threaded_scan(

            target,

            ports,

            timeout,

            allow_reserved_ports,

            workers

        )

    elif mode == "m":

        print(
            Colour.CYAN +
            "\nStarting multiprocessing scan...\n" +
            Colour.RESET
        )

        results = process_scan(

            target,

            ports,

            timeout,

            allow_reserved_ports,

            workers

        )

    else:

        print(
            Colour.CYAN +
            "\nStarting sequential scan...\n" +
            Colour.RESET
        )

        results = sequential_scan(

            target,

            ports,

            timeout,

            allow_reserved_ports

        )

    duration = datetime.now() - start

    print()

    print(

        Colour.GREEN +

        f"Scan completed in {duration.total_seconds():.2f} seconds."

        + Colour.RESET

    )

    return results

# ============================================================
# Result Filtering
# ============================================================

def filter_results(results, mode):

    if mode == "all":

        return results

    filtered = []

    keyword = mode.lower()

    for port, state in results:

        if keyword in state.lower():

            filtered.append((port, state))

    return filtered

# ============================================================
# Open Port Helper
# ============================================================

def get_open_ports(results):

    return [

        port

        for port, state in results

        if state.lower().startswith("open")

    ]
    # ============================================================
# Nmap Helper
# ============================================================

def get_nmap():

    try:

        return nmap.PortScanner()

    except Exception as e:

        print(
            Colour.RED +
            f"\nUnable to start Nmap:\n{e}" +
            Colour.RESET
        )

        return None


# ============================================================
# Service Detection
# ============================================================

def detect_services(
    target,
    open_ports
):

    if not open_ports:

        return {}

    scanner = get_nmap()

    if scanner is None:

        return {}

    port_string = ",".join(map(str, open_ports))

    print()

    print(
        Colour.CYAN +
        "Running Nmap service detection..." +
        Colour.RESET
    )

    services = {}

    try:

        scanner.scan(
            hosts=target,
            ports=port_string,
            arguments="-sV"
        )

        if target not in scanner.all_hosts():

            return {}

        tcp = scanner[target].get("tcp", {})

        for port, info in tcp.items():

            services[port] = {

                "service": info.get("name", "Unknown"),

                "product": info.get("product", ""),

                "version": info.get("version", ""),

                "extra": info.get("extrainfo", ""),

                "cpe": info.get("cpe", "")

            }

    except Exception as e:

        print(
            Colour.RED +
            str(e) +
            Colour.RESET
        )

    return services


# ============================================================
# Banner Grabbing
# ============================================================

def grab_banner(
    target,
    port,
    timeout=2
):

    try:

        sock = socket.create_connection(
            (target, port),
            timeout=timeout
        )

        sock.settimeout(timeout)

        banner = sock.recv(1024)

        sock.close()

        return banner.decode(
            errors="ignore"
        ).strip()

    except Exception:

        return ""


# ============================================================
# Banner Detection
# ============================================================

def collect_banners(
    target,
    open_ports
):

    banners = {}

    print()

    print(
        Colour.CYAN +
        "Collecting banners..." +
        Colour.RESET
    )

    for port in open_ports:

        banners[port] = grab_banner(
            target,
            port
        )

    return banners


# ============================================================
# Vulnerability Scan
# ============================================================

def vulnerability_scan(
    target,
    open_ports
):

    if not open_ports:

        return {}

    scanner = get_nmap()

    if scanner is None:

        return {}

    ports = ",".join(
        map(str, open_ports)
    )

    print()

    print(
        Colour.CYAN +
        "Running vulnerability scan..." +
        Colour.RESET
    )

    findings = {}

    try:

        scanner.scan(

            hosts=target,

            ports=ports,

            arguments="--script vulners,vulscan"

        )

        if target not in scanner.all_hosts():

            return findings

        tcp = scanner[target].get("tcp", {})

        for port, info in tcp.items():

            scripts = info.get("script", {})

            findings[port] = scripts

    except Exception as e:

        print(

            Colour.RED +

            str(e)

            + Colour.RESET

        )

    return findings


# ============================================================
# Optional OS Detection
# ============================================================

def detect_os(target):

    scanner = get_nmap()

    if scanner is None:

        return "Unknown"

    try:

        scanner.scan(

            hosts=target,

            arguments="-O"

        )

        matches = scanner[target].get(
            "osmatch",
            []
        )

        if matches:

            return matches[0]["name"]

    except Exception:

        pass

    return "Unknown"


# ============================================================
# Display Services
# ============================================================

def display_services(services):

    if not services:

        return

    print()

    print("=" * 90)

    print("Detected Services")

    print("=" * 90)

    print(

        f"{'Port':<8}"

        f"{'Service':<15}"

        f"{'Product':<25}"

        f"{'Version':<20}"

    )

    print("-" * 90)

    for port in sorted(services):

        item = services[port]

        print(

            f"{port:<8}"

            f"{item['service']:<15}"

            f"{item['product']:<25}"

            f"{item['version']:<20}"

        )


# ============================================================
# Display Vulnerabilities
# ============================================================

def display_vulnerabilities(vulns):

    if not vulns:

        return

    print()

    print("=" * 90)

    print("Security Findings")

    print("=" * 90)

    found = False

    for port in sorted(vulns):

        scripts = vulns[port]

        if not scripts:

            continue

        found = True

        print()

        print(f"Port {port}")

        print("-" * 40)

        for script, output in scripts.items():

            print()

            print(script)

            print(output)

    if not found:

        print("No vulnerabilities reported.")


# ============================================================
# Display Banners
# ============================================================

def display_banners(banners):

    if not banners:

        return

    print()

    print("=" * 90)

    print("Collected Banners")

    print("=" * 90)

    for port in sorted(banners):

        if banners[port]:

            print()

            print(f"{port}")

            print(banners[port])
            # ============================================================
# Scan Result Display
# ============================================================

def display_results(
    target,
    results,
    services=None
):

    services = services or {}

    print()

    print("=" * 110)
    print(f"Scan Results - {target}")
    print("=" * 110)

    print(
        f"{'Port':<8}"
        f"{'State':<18}"
        f"{'Service':<18}"
        f"{'Product':<30}"
        f"{'Version':<20}"
    )

    print("-" * 110)

    for port, state in sorted(results):

        info = services.get(port, {})

        service = info.get("service", "-")
        product = info.get("product", "-")
        version = info.get("version", "-")

        colour = Colour.RESET

        if state.startswith("Open"):
            colour = Colour.GREEN

        elif state.startswith("Closed"):
            colour = Colour.RED

        elif state.startswith("Filtered"):
            colour = Colour.YELLOW

        elif state.startswith("Skipped"):
            colour = Colour.BLUE

        print(
            colour +
            f"{port:<8}"
            f"{state:<18}"
            f"{service:<18}"
            f"{product:<30}"
            f"{version:<20}"
            + Colour.RESET
        )


# ============================================================
# Logging
# ============================================================

def log_results(
    logger,
    target,
    results,
    services=None
):

    services = services or {}

    logger.info("=" * 80)
    logger.info("Scan Results")
    logger.info("=" * 80)

    for port, state in sorted(results):

        info = services.get(port, {})

        logger.info(
            "%s | %-5d | %-12s | %-12s | %-20s | %-20s",
            target,
            port,
            state,
            info.get("service", ""),
            info.get("product", ""),
            info.get("version", "")
        )


# ============================================================
# CSV Export
# ============================================================

def export_csv(

    filename,

    target,

    results,

    services=None,

    vulnerabilities=None

):

    services = services or {}

    vulnerabilities = vulnerabilities or {}

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([

            "Target",

            "Port",

            "State",

            "Service",

            "Product",

            "Version",

            "CPE",

            "Vulnerabilities"

        ])

        for port, state in sorted(results):

            info = services.get(port, {})

            vuln_text = ""

            if port in vulnerabilities:

                vuln_text = " | ".join(

                    vulnerabilities[port].keys()

                )

            writer.writerow([

                target,

                port,

                state,

                info.get("service", ""),

                info.get("product", ""),

                info.get("version", ""),

                info.get("cpe", ""),

                vuln_text

            ])

    print()

    print(

        Colour.GREEN +

        f"CSV exported to:\n{filename}"

        + Colour.RESET

    )


# ============================================================
# Statistics
# ============================================================

def scan_statistics(results):

    stats = {

        "open": 0,

        "closed": 0,

        "filtered": 0,

        "skipped": 0,

        "error": 0

    }

    for _, state in results:

        state = state.lower()

        if state.startswith("open"):

            stats["open"] += 1

        elif state.startswith("closed"):

            stats["closed"] += 1

        elif state.startswith("filtered"):

            stats["filtered"] += 1

        elif state.startswith("skipped"):

            stats["skipped"] += 1

        else:

            stats["error"] += 1

    return stats


# ============================================================
# Statistics Display
# ============================================================

def display_statistics(stats):

    print()

    print("=" * 45)

    print("Scan Summary")

    print("=" * 45)

    print(

        Colour.GREEN +

        f"Open Ports      : {stats['open']}"

        + Colour.RESET

    )

    print(

        Colour.RED +

        f"Closed Ports    : {stats['closed']}"

        + Colour.RESET

    )

    print(

        Colour.YELLOW +

        f"Filtered Ports  : {stats['filtered']}"

        + Colour.RESET

    )

    print(

        Colour.BLUE +

        f"Skipped Ports   : {stats['skipped']}"

        + Colour.RESET

    )

    print(

        f"Errors          : {stats['error']}"

    )


# ============================================================
# Scan Summary
# ============================================================

def save_scan_summary(

    filename,

    target,

    stats,

    elapsed

):

    with open(filename, "w", encoding="utf-8") as f:

        f.write("=" * 60 + "\n")

        f.write("Python Port Scanner Summary\n")

        f.write("=" * 60 + "\n\n")

        f.write(f"Target: {target}\n")

        f.write(f"Date: {datetime.now()}\n")

        f.write(f"Elapsed Time: {elapsed:.2f} seconds\n\n")

        f.write(f"Open Ports: {stats['open']}\n")

        f.write(f"Closed Ports: {stats['closed']}\n")

        f.write(f"Filtered Ports: {stats['filtered']}\n")

        f.write(f"Skipped Ports: {stats['skipped']}\n")

        f.write(f"Errors: {stats['error']}\n")


# ============================================================
# Output Menu
# ============================================================

def ask_output_options():

    export = (

        input(

            "\nExport CSV? (y/n): "

        ).lower()

        == "y"

    )

    summary = (

        input(

            "Save scan summary? (y/n): "

        ).lower()

        == "y"

    )

    return export, summary


# ============================================================
# Filter Menu
# ============================================================

def get_filter_mode():

    while True:

        mode = input(

            "\nDisplay (open/closed/all): "

        ).lower()

        if mode in ("open", "closed", "all"):

            return mode

        print("Invalid option.")


# ============================================================
# Display Filter
# ============================================================

def apply_display_filter(results, mode):

    if mode == "all":

        return results

    filtered = []

    for port, state in results:

        if mode in state.lower():

            filtered.append((port, state))

    return filtered
    # ============================================================
# Yes/No Input Helper
# ============================================================

def ask_yes_no(prompt, default=False):

    while True:

        suffix = " [Y/n]: " if default else " [y/N]: "

        answer = input(prompt + suffix).strip().lower()

        if not answer:
            return default

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter 'y' or 'n'.")


# ============================================================
# Port Range Helper
# ============================================================

def get_port_range():

    while True:

        start_port = validate_port(
            input("Enter starting port: ").strip()
        )

        end_port = validate_port(
            input("Enter ending port: ").strip()
        )

        if start_port is None or end_port is None:

            print(
                Colour.RED +
                "Ports must be between 1 and 65535." +
                Colour.RESET
            )

            continue

        if start_port > end_port:

            print(
                Colour.RED +
                "The starting port cannot exceed the ending port." +
                Colour.RESET
            )

            continue

        return list(range(start_port, end_port + 1))


# ============================================================
# Custom Ports
# ============================================================

def get_custom_ports():

    while True:

        raw = input(
            "\nEnter ports separated by spaces or commas: "
        ).strip()

        raw_ports = raw.replace(",", " ").split()

        valid_ports = []
        invalid_ports = []

        for value in raw_ports:

            port = validate_port(value)

            if port is None:
                invalid_ports.append(value)
            else:
                valid_ports.append(port)

        if invalid_ports:

            print(
                Colour.RED +
                "Invalid port value(s): " +
                ", ".join(invalid_ports) +
                Colour.RESET
            )

            continue

        if not valid_ports:

            print(
                Colour.RED +
                "Enter at least one valid port." +
                Colour.RESET
            )

            continue

        return sorted(set(valid_ports))


# ============================================================
# Scan Type Menu
# ============================================================

def get_scan_ports():

    while True:

        print("\nChoose the type of scan:")
        print("  (s) Standard scan")
        print("  (c) Custom-port scan")
        print("  (q) Quick scan")
        print("  (t) Thorough scan")
        print("  (x) Exit")

        choice = input(
            "Enter your choice (s/c/q/t/x): "
        ).strip().lower()

        if choice == "s":

            ports = get_port_range()

            return ports, "Standard"

        if choice == "c":

            ports = get_custom_ports()

            return ports, "Custom"

        if choice == "q":

            return sorted(set(COMMON_PORTS)), "Quick"

        if choice == "t":

            confirmation = ask_yes_no(
                "A thorough scan checks all 65,535 ports. Continue?"
            )

            if confirmation:
                return list(range(1, 65536)), "Thorough"

        elif choice == "x":

            return None, None

        else:

            print(
                Colour.RED +
                "Invalid scan type." +
                Colour.RESET
            )


# ============================================================
# Scan Execution Mode
# ============================================================

def get_execution_mode():

    while True:

        print("\nChoose the scanning method:")
        print("  (t) Multithreading")
        print("  (m) Multiprocessing")
        print("  (s) Sequential")

        choice = input(
            "Enter your choice (t/m/s): "
        ).strip().lower()

        if choice in ("t", "m", "s"):
            return choice

        print(
            Colour.RED +
            "Invalid scanning method." +
            Colour.RESET
        )


# ============================================================
# Prepare Output Directory
# ============================================================

def prepare_output_directory():

    try:

        DOWNLOAD_FOLDER.mkdir(
            parents=True,
            exist_ok=True
        )

        return DOWNLOAD_FOLDER

    except OSError:

        fallback = Path.cwd() / "scan_results"

        fallback.mkdir(
            parents=True,
            exist_ok=True
        )

        return fallback


# ============================================================
# Safe Filename Helper
# ============================================================

def safe_filename(value):

    safe_characters = []

    for character in value:

        if character.isalnum() or character in ("-", "_", "."):
            safe_characters.append(character)
        else:
            safe_characters.append("_")

    return "".join(safe_characters)


# ============================================================
# Output File Paths
# ============================================================

def create_output_paths(target, output_directory):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safe_target = safe_filename(target)

    base_name = (
        f"{safe_target}_{timestamp}"
    )

    return {

        "csv": output_directory / (
            base_name + "_results.csv"
        ),

        "summary": output_directory / (
            base_name + "_summary.txt"
        )
    }


# ============================================================
# Target Resolution
# ============================================================

def resolve_target(target):

    try:

        address_info = socket.getaddrinfo(
            target,
            None,
            type=socket.SOCK_STREAM
        )

        addresses = []

        for item in address_info:

            address = item[4][0]

            if address not in addresses:
                addresses.append(address)

        return addresses

    except socket.gaierror:

        return []


# ============================================================
# Display Target Information
# ============================================================

def display_target_information(target):

    addresses = resolve_target(target)

    print()
    print("=" * 60)
    print(f"Target: {target}")

    if addresses:

        print(
            "Resolved address(es): " +
            ", ".join(addresses)
        )

    print("=" * 60)


# ============================================================
# Merge Banners into Services
# ============================================================

def merge_banners_into_services(
    services,
    banners
):

    for port, banner in banners.items():

        services.setdefault(
            port,
            {
                "service": "Unknown",
                "product": "",
                "version": "",
                "extra": "",
                "cpe": ""
            }
        )

        services[port]["banner"] = banner

    return services


# ============================================================
# Log Vulnerability Findings
# ============================================================

def log_vulnerabilities(
    logger,
    target,
    vulnerabilities
):

    if not vulnerabilities:

        logger.info(
            "No vulnerability-script findings were returned."
        )

        return

    finding_count = 0

    for port, scripts in sorted(
        vulnerabilities.items()
    ):

        for script_name, output in scripts.items():

            finding_count += 1

            logger.warning(
                "%s | Port %s | Script %s | %s",
                target,
                port,
                script_name,
                str(output).replace("\n", " ")
            )

    if finding_count == 0:

        logger.info(
            "No vulnerability-script findings were returned."
        )


# ============================================================
# Scan One Target
# ============================================================

def scan_target(
    target,
    ports,
    scan_name,
    mode,
    timeout,
    workers,
    allow_reserved_ports,
    filter_mode,
    enable_service_detection,
    enable_banner_collection,
    enable_security_scan,
    enable_os_detection,
    export_results,
    save_summary
):

    output_directory = prepare_output_directory()

    logger = configure_logger(target)

    output_paths = create_output_paths(
        target,
        output_directory
    )

    display_target_information(target)

    logger.info(
        "Starting %s scan against %s",
        scan_name,
        target
    )

    logger.info(
        "Ports requested: %d",
        len(ports)
    )

    logger.info(
        "Execution mode: %s",
        mode
    )

    logger.info(
        "Socket timeout: %.2f seconds",
        timeout
    )

    logger.info(
        "Workers: %d",
        workers
    )

    scan_started = datetime.now()

    results = run_scan(
        target=target,
        ports=ports,
        timeout=timeout,
        allow_reserved_ports=allow_reserved_ports,
        workers=workers,
        mode=mode
    )

    elapsed = (
        datetime.now() - scan_started
    ).total_seconds()

    open_ports = get_open_ports(results)

    services = {}
    banners = {}
    vulnerabilities = {}

    if enable_service_detection and open_ports:

        services = detect_services(
            target,
            open_ports
        )

    if enable_banner_collection and open_ports:

        banners = collect_banners(
            target,
            open_ports
        )

        services = merge_banners_into_services(
            services,
            banners
        )

    if enable_security_scan and open_ports:

        vulnerabilities = vulnerability_scan(
            target,
            open_ports
        )

    detected_os = None

    if enable_os_detection:

        print(
            Colour.CYAN +
            "\nRunning OS detection..." +
            Colour.RESET
        )

        detected_os = detect_os(target)

        print(
            f"Detected operating system: "
            f"{detected_os}"
        )

        logger.info(
            "Detected operating system: %s",
            detected_os
        )

    displayed_results = apply_display_filter(
        results,
        filter_mode
    )

    if displayed_results:

        display_results(
            target,
            displayed_results,
            services
        )

    else:

        print(
            Colour.YELLOW +
            f"\nNo results matched the "
            f"'{filter_mode}' filter." +
            Colour.RESET
        )

    if services:

        display_services(services)

    if banners:

        display_banners(banners)

    if enable_security_scan:

        display_vulnerabilities(
            vulnerabilities
        )

    stats = scan_statistics(results)

    display_statistics(stats)

    print(
        f"\nElapsed time     : "
        f"{elapsed:.2f} seconds"
    )

    print(
        f"Ports scanned    : "
        f"{len(results)}"
    )

    print(
        f"Open port list   : "
        f"{', '.join(map(str, open_ports)) "
        f"if open_ports else 'None'}"
    )

    log_results(
        logger,
        target,
        results,
        services
    )

    log_vulnerabilities(
        logger,
        target,
        vulnerabilities
    )

    logger.info(
        "Scan elapsed time: %.2f seconds",
        elapsed
    )

    if export_results:

        export_csv(
            filename=output_paths["csv"],
            target=target,
            results=results,
            services=services,
            vulnerabilities=vulnerabilities
        )

    if save_summary:

        save_scan_summary(
            filename=output_paths["summary"],
            target=target,
            stats=stats,
            elapsed=elapsed
        )

        print(
            Colour.GREEN +
            "\nSummary saved to:\n"
            f"{output_paths['summary']}" +
            Colour.RESET
        )

    print(
        Colour.GREEN +
        f"\nFinished scanning {target}." +
        Colour.RESET
    )


# ============================================================
# Main Function
# ============================================================

def main():

    print_banner()

    print(
        "Scan only systems that you own or are "
        "authorised to test."
    )

    targets = get_targets()

    ports, scan_name = get_scan_ports()

    if ports is None:

        print("\nExiting scanner.")

        return

    execution_mode = get_execution_mode()

    timeout = get_timeout()

    if timeout <= 0:

        timeout = DEFAULT_TIMEOUT

    workers = get_workers()

    # Avoid creating an excessive number of local workers.
    workers = min(workers, 500)

    allow_reserved_ports = ask_yes_no(
        "Allow scanning reserved ports (1-1023)?",
        default=True
    )

    filter_mode = get_filter_mode()

    enable_service_detection = ask_yes_no(
        "Perform Nmap service/version detection?"
    )

    enable_banner_collection = ask_yes_no(
        "Attempt passive banner collection?"
    )

    enable_security_scan = ask_yes_no(
        "Run authorised Nmap vulnerability scripts?"
    )

    enable_os_detection = ask_yes_no(
        "Attempt Nmap OS detection?"
    )

    export_results, save_summary = (
        ask_output_options()
    )

    print()
    print("=" * 60)
    print("Scan Configuration")
    print("=" * 60)
    print(f"Targets             : {len(targets)}")
    print(f"Scan type           : {scan_name}")
    print(f"Ports requested     : {len(ports)}")
    print(f"Execution mode      : {execution_mode}")
    print(f"Workers             : {workers}")
    print(f"Timeout             : {timeout:.2f}s")
    print(f"Result filter       : {filter_mode}")
    print(
        f"Service detection   : "
        f"{enable_service_detection}"
    )
    print(
        f"Banner collection   : "
        f"{enable_banner_collection}"
    )
    print(
        f"Security scripts    : "
        f"{enable_security_scan}"
    )
    print(
        f"OS detection        : "
        f"{enable_os_detection}"
    )
    print("=" * 60)

    if not ask_yes_no(
        "Start the scan?",
        default=True
    ):

        print("\nScan cancelled.")

        return

    overall_started = datetime.now()

    for target in targets:

        try:

            scan_target(
                target=target,
                ports=ports,
                scan_name=scan_name,
                mode=execution_mode,
                timeout=timeout,
                workers=workers,
                allow_reserved_ports=allow_reserved_ports,
                filter_mode=filter_mode,
                enable_service_detection=(
                    enable_service_detection
                ),
                enable_banner_collection=(
                    enable_banner_collection
                ),
                enable_security_scan=(
                    enable_security_scan
                ),
                enable_os_detection=(
                    enable_os_detection
                ),
                export_results=export_results,
                save_summary=save_summary
            )

        except KeyboardInterrupt:

            print(
                Colour.YELLOW +
                "\nScan interrupted by the user." +
                Colour.RESET
            )

            break

        except Exception as error:

            logging.exception(
                "Unexpected error while scanning %s",
                target
            )

            print(
                Colour.RED +
                f"\nUnexpected error while scanning "
                f"{target}: {error}" +
                Colour.RESET
            )

    total_elapsed = (
        datetime.now() - overall_started
    ).total_seconds()

    print()
    print("=" * 60)
    print(
        f"All scans finished in "
        f"{total_elapsed:.2f} seconds."
    )
    print("=" * 60)


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            Colour.YELLOW +
            "\nProgram stopped by the user." +
            Colour.RESET
