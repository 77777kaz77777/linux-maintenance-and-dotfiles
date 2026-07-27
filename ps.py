#!/usr/bin/env python3
"""Interactive Python port scanner.

Use only on systems you own or are authorised to test.
Requires:
    pip install python-nmap
    nmap installed on the operating system
"""

from __future__ import annotations

import concurrent.futures
import csv
import ipaddress
import logging
import os
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:
    import nmap
except ImportError:
    nmap = None  # type: ignore[assignment]


COMMON_PORTS = sorted(
    {
        20, 21, 22, 23, 25, 53, 69, 80, 110, 123, 143, 161, 389, 443,
        445, 587, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379,
        8080,
    }
)

SECURITY_PORTS: Mapping[int, str] = {
    21: "FTP",
    23: "Telnet",
    69: "TFTP",
}

RESERVED_PORTS = range(1, 1024)
DEFAULT_TIMEOUT = 1.0
DEFAULT_WORKERS = 100
MAX_WORKERS = 500
OUTPUT_DIRECTORY = Path.home() / "Downloads"


class Colour:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


@dataclass(frozen=True)
class PortResult:
    port: int
    state: str


@dataclass
class ServiceInfo:
    service: str = "Unknown"
    product: str = ""
    version: str = ""
    extra: str = ""
    cpe: str = ""
    banner: str = ""


@dataclass
class ScanOptions:
    timeout: float
    workers: int
    mode: str
    allow_reserved_ports: bool
    filter_mode: str
    service_detection: bool
    banner_collection: bool
    vulnerability_scan: bool
    os_detection: bool
    export_csv: bool
    save_summary: bool


def supports_colour() -> bool:
    return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"


def colourise(text: str, colour: str) -> str:
    return f"{colour}{text}{Colour.RESET}" if supports_colour() else text


def safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in value)


def prepare_output_directory() -> Path:
    try:
        OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
        return OUTPUT_DIRECTORY
    except OSError:
        fallback = Path.cwd() / "scan_results"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def configure_logger(target: str) -> Tuple[logging.Logger, Path]:
    output_dir = prepare_output_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_target = safe_filename(target)
    log_path = output_dir / f"{safe_target}_{timestamp}_scan.log"

    logger = logging.getLogger(f"port_scanner.{safe_target}.{timestamp}")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger, log_path


def print_banner() -> None:
    print("\n" + "=" * 64)
    print("                 PROFESSIONAL PYTHON PORT SCANNER")
    print("=" * 64)
    print("Scan only systems that you own or are authorised to test.")


def validate_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def validate_hostname(hostname: str) -> bool:
    if not hostname or len(hostname) > 253:
        return False
    try:
        socket.getaddrinfo(hostname, None)
        return True
    except socket.gaierror:
        return False


def validate_target(target: str) -> bool:
    return validate_ip(target) or validate_hostname(target)


def validate_port(value: str) -> Optional[int]:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return None
    return port if 1 <= port <= 65535 else None


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        answer = input(prompt + suffix).strip().lower()
        if not answer:
            return default
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter y or n.")


def get_targets() -> List[str]:
    while True:
        values = input("\nEnter IP address(es) or hostname(s), separated by spaces: ").split()
        if not values:
            print("Enter at least one target.")
            continue
        invalid = [target for target in values if not validate_target(target)]
        if invalid:
            print(colourise("Invalid target(s): " + ", ".join(invalid), Colour.RED))
            continue
        return list(dict.fromkeys(values))


def get_timeout() -> float:
    value = input(f"Socket timeout [{DEFAULT_TIMEOUT}s]: ").strip()
    if not value:
        return DEFAULT_TIMEOUT
    try:
        timeout = float(value)
        return timeout if timeout > 0 else DEFAULT_TIMEOUT
    except ValueError:
        return DEFAULT_TIMEOUT


def get_workers() -> int:
    value = input(f"Worker count [{DEFAULT_WORKERS}]: ").strip()
    if not value:
        return DEFAULT_WORKERS
    try:
        return min(max(int(value), 1), MAX_WORKERS)
    except ValueError:
        return DEFAULT_WORKERS


def get_port_range() -> List[int]:
    while True:
        start = validate_port(input("Enter starting port: ").strip())
        end = validate_port(input("Enter ending port: ").strip())
        if start is None or end is None:
            print("Ports must be between 1 and 65535.")
        elif start > end:
            print("Starting port cannot exceed ending port.")
        else:
            return list(range(start, end + 1))


def get_custom_ports() -> List[int]:
    while True:
        raw_values = input("Enter ports separated by spaces or commas: ").replace(",", " ").split()
        ports = [validate_port(value) for value in raw_values]
        if not raw_values or any(port is None for port in ports):
            print("Enter only valid ports between 1 and 65535.")
            continue
        return sorted(set(port for port in ports if port is not None))


def get_scan_ports() -> Tuple[Optional[List[int]], Optional[str]]:
    while True:
        print("\nChoose scan type:")
        print("  (s) Standard range")
        print("  (c) Custom ports")
        print("  (q) Quick common-port scan")
        print("  (t) Thorough scan (1-65535)")
        print("  (x) Exit")
        choice = input("Choice: ").strip().lower()
        if choice == "s":
            return get_port_range(), "Standard"
        if choice == "c":
            return get_custom_ports(), "Custom"
        if choice == "q":
            return COMMON_PORTS.copy(), "Quick"
        if choice == "t":
            if ask_yes_no("Scan all 65,535 ports?", default=False):
                return list(range(1, 65536)), "Thorough"
        elif choice == "x":
            return None, None
        else:
            print("Invalid choice.")


def get_execution_mode() -> str:
    while True:
        print("\nChoose execution mode:")
        print("  (t) Multithreading")
        print("  (m) Multiprocessing")
        print("  (s) Sequential")
        choice = input("Choice: ").strip().lower()
        if choice in {"t", "m", "s"}:
            return choice
        print("Invalid choice.")


def get_filter_mode() -> str:
    while True:
        choice = input("Display results (open/closed/all): ").strip().lower()
        if choice in {"open", "closed", "all"}:
            return choice
        print("Invalid choice.")


def print_progress(current: int, total: int) -> None:
    if total <= 0:
        return
    width = 36
    fraction = current / total
    filled = int(width * fraction)
    bar = "█" * filled + "-" * (width - filled)
    print(f"\r[{bar}] {current}/{total} ({fraction * 100:5.1f}%)", end="", flush=True)


def scan_port(args: Tuple[str, int, float, bool]) -> PortResult:
    target, port, timeout, allow_reserved_ports = args
    if port in RESERVED_PORTS and not allow_reserved_ports:
        return PortResult(port, "Skipped (Reserved Port)")
    try:
        with socket.create_connection((target, port), timeout=timeout):
            if port in SECURITY_PORTS:
                return PortResult(port, f"Open (Security Risk - {SECURITY_PORTS[port]})")
            return PortResult(port, "Open")
    except ConnectionRefusedError:
        return PortResult(port, "Closed")
    except socket.timeout:
        return PortResult(port, "Filtered")
    except socket.gaierror:
        return PortResult(port, "Error (Name Resolution Failed)")
    except OSError as error:
        return PortResult(port, f"Error ({error.strerror or error})")


def run_scan(
    target: str,
    ports: Sequence[int],
    timeout: float,
    allow_reserved_ports: bool,
    workers: int,
    mode: str,
) -> Tuple[List[PortResult], float]:
    arguments = [(target, port, timeout, allow_reserved_ports) for port in ports]
    results: List[PortResult] = []
    started = datetime.now()

    if mode == "s":
        for index, item in enumerate(arguments, start=1):
            results.append(scan_port(item))
            print_progress(index, len(arguments))
    else:
        executor_class = (
            concurrent.futures.ThreadPoolExecutor
            if mode == "t"
            else concurrent.futures.ProcessPoolExecutor
        )
        with executor_class(max_workers=workers) as executor:
            futures = [executor.submit(scan_port, item) for item in arguments]
            for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                try:
                    results.append(future.result())
                except Exception as error:
                    item = arguments[index - 1]
                    results.append(PortResult(item[1], f"Error ({error})"))
                print_progress(index, len(arguments))

    print()
    results.sort(key=lambda result: result.port)
    elapsed = (datetime.now() - started).total_seconds()
    print(colourise(f"Socket scan completed in {elapsed:.2f} seconds.", Colour.GREEN))
    return results, elapsed


def filter_results(results: Sequence[PortResult], mode: str) -> List[PortResult]:
    if mode == "all":
        return list(results)
    return [result for result in results if result.state.lower().startswith(mode)]


def get_open_ports(results: Sequence[PortResult]) -> List[int]:
    return [result.port for result in results if result.state.lower().startswith("open")]


def get_nmap_scanner() -> Optional[object]:
    if nmap is None:
        print(colourise("python-nmap is not installed. Run: pip install python-nmap", Colour.RED))
        return None
    try:
        return nmap.PortScanner()
    except Exception as error:
        print(colourise(f"Unable to start Nmap: {error}", Colour.RED))
        return None


def detect_services(target: str, open_ports: Sequence[int]) -> Dict[int, ServiceInfo]:
    if not open_ports:
        return {}
    scanner = get_nmap_scanner()
    if scanner is None:
        return {}
    print(colourise("Running Nmap service/version detection...", Colour.CYAN))
    services: Dict[int, ServiceInfo] = {}
    try:
        scanner.scan(hosts=target, ports=",".join(map(str, open_ports)), arguments="-sV")
        if target not in scanner.all_hosts():
            return services
        for port, info in scanner[target].get("tcp", {}).items():
            services[int(port)] = ServiceInfo(
                service=info.get("name", "Unknown"),
                product=info.get("product", ""),
                version=info.get("version", ""),
                extra=info.get("extrainfo", ""),
                cpe=info.get("cpe", ""),
            )
    except Exception as error:
        print(colourise(f"Service detection failed: {error}", Colour.RED))
    return services


def grab_banner(target: str, port: int, timeout: float = 2.0) -> str:
    try:
        with socket.create_connection((target, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            data = sock.recv(1024)
            return data.decode(errors="ignore").strip()
    except (OSError, socket.timeout):
        return ""


def collect_banners(target: str, open_ports: Sequence[int], workers: int) -> Dict[int, str]:
    if not open_ports:
        return {}
    print(colourise("Collecting passive service banners...", Colour.CYAN))
    banners: Dict[int, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(workers, 50)) as executor:
        future_map = {executor.submit(grab_banner, target, port): port for port in open_ports}
        for future in concurrent.futures.as_completed(future_map):
            port = future_map[future]
            try:
                banners[port] = future.result()
            except Exception:
                banners[port] = ""
    return banners


def vulnerability_scan(target: str, open_ports: Sequence[int]) -> Dict[int, Dict[str, str]]:
    if not open_ports:
        return {}
    scanner = get_nmap_scanner()
    if scanner is None:
        return {}
    print(colourise("Running authorised Nmap vulnerability scripts...", Colour.CYAN))
    findings: Dict[int, Dict[str, str]] = {}
    try:
        scanner.scan(
            hosts=target,
            ports=",".join(map(str, open_ports)),
            arguments="-sV --script vulners,vulscan",
        )
        if target not in scanner.all_hosts():
            return findings
        for port, info in scanner[target].get("tcp", {}).items():
            scripts = info.get("script", {})
            findings[int(port)] = {str(name): str(output) for name, output in scripts.items()}
    except Exception as error:
        print(colourise(f"Vulnerability scan failed: {error}", Colour.RED))
    return findings


def detect_os(target: str) -> str:
    scanner = get_nmap_scanner()
    if scanner is None:
        return "Unknown"
    print(colourise("Running Nmap OS detection...", Colour.CYAN))
    try:
        scanner.scan(hosts=target, arguments="-O")
        if target not in scanner.all_hosts():
            return "Unknown"
        matches = scanner[target].get("osmatch", [])
        return matches[0].get("name", "Unknown") if matches else "Unknown"
    except Exception as error:
        return f"Unknown ({error})"


def display_target_information(target: str) -> None:
    print("\n" + "=" * 64)
    print(f"Target: {target}")
    try:
        addresses = sorted({item[4][0] for item in socket.getaddrinfo(target, None)})
        if addresses:
            print("Resolved address(es): " + ", ".join(addresses))
    except socket.gaierror:
        pass
    print("=" * 64)


def display_results(
    target: str,
    results: Sequence[PortResult],
    services: Mapping[int, ServiceInfo],
) -> None:
    print("\n" + "=" * 112)
    print(f"Scan Results - {target}")
    print("=" * 112)
    print(f"{'Port':<8}{'State':<36}{'Service':<16}{'Product':<28}{'Version':<20}")
    print("-" * 112)
    for result in results:
        service = services.get(result.port, ServiceInfo())
        row = (
            f"{result.port:<8}{result.state:<36}{service.service:<16}"
            f"{service.product:<28}{service.version:<20}"
        )
        if result.state.startswith("Open"):
            row = colourise(row, Colour.GREEN)
        elif result.state.startswith("Closed"):
            row = colourise(row, Colour.RED)
        elif result.state.startswith("Filtered"):
            row = colourise(row, Colour.YELLOW)
        elif result.state.startswith("Skipped"):
            row = colourise(row, Colour.BLUE)
        print(row)


def display_banners(banners: Mapping[int, str]) -> None:
    non_empty = {port: banner for port, banner in banners.items() if banner}
    if not non_empty:
        print("\nNo passive banners were returned.")
        return
    print("\n" + "=" * 88)
    print("Collected Banners")
    print("=" * 88)
    for port in sorted(non_empty):
        print(f"\nPort {port}\n{'-' * 40}\n{non_empty[port]}")


def display_vulnerabilities(findings: Mapping[int, Mapping[str, str]]) -> None:
    non_empty = {port: scripts for port, scripts in findings.items() if scripts}
    print("\n" + "=" * 88)
    print("Security Findings")
    print("=" * 88)
    if not non_empty:
        print("No vulnerability-script findings were returned.")
        return
    for port in sorted(non_empty):
        print(f"\nPort {port}\n{'-' * 40}")
        for script_name, output in non_empty[port].items():
            print(f"\n[{script_name}]\n{output}")


def scan_statistics(results: Sequence[PortResult]) -> Dict[str, int]:
    stats = {"open": 0, "closed": 0, "filtered": 0, "skipped": 0, "error": 0}
    for result in results:
        state = result.state.lower()
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


def display_statistics(stats: Mapping[str, int]) -> None:
    print("\n" + "=" * 48)
    print("Scan Summary")
    print("=" * 48)
    print(colourise(f"Open ports      : {stats['open']}", Colour.GREEN))
    print(colourise(f"Closed ports    : {stats['closed']}", Colour.RED))
    print(colourise(f"Filtered ports  : {stats['filtered']}", Colour.YELLOW))
    print(colourise(f"Skipped ports   : {stats['skipped']}", Colour.BLUE))
    print(f"Errors          : {stats['error']}")


def create_output_paths(target: str) -> Dict[str, Path]:
    output_dir = prepare_output_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"{safe_filename(target)}_{timestamp}"
    return {
        "csv": output_dir / f"{base}_results.csv",
        "summary": output_dir / f"{base}_summary.txt",
    }


def export_results_csv(
    path: Path,
    target: str,
    results: Sequence[PortResult],
    services: Mapping[int, ServiceInfo],
    vulnerabilities: Mapping[int, Mapping[str, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(
            [
                "Target", "Port", "State", "Service", "Product", "Version",
                "Extra", "CPE", "Banner", "Vulnerability Scripts",
            ]
        )
        for result in results:
            service = services.get(result.port, ServiceInfo())
            scripts = " | ".join(vulnerabilities.get(result.port, {}).keys())
            writer.writerow(
                [
                    target,
                    result.port,
                    result.state,
                    service.service,
                    service.product,
                    service.version,
                    service.extra,
                    service.cpe,
                    service.banner,
                    scripts,
                ]
            )


def save_summary(
    path: Path,
    target: str,
    stats: Mapping[str, int],
    elapsed: float,
    open_ports: Sequence[int],
    detected_os: str,
) -> None:
    open_port_text = ", ".join(map(str, open_ports)) if open_ports else "None"
    with path.open("w", encoding="utf-8") as summary_file:
        summary_file.write("=" * 64 + "\n")
        summary_file.write("Python Port Scanner Summary\n")
        summary_file.write("=" * 64 + "\n")
        summary_file.write(f"Target: {target}\n")
        summary_file.write(f"Date: {datetime.now().isoformat(sep=' ', timespec='seconds')}\n")
        summary_file.write(f"Elapsed time: {elapsed:.2f} seconds\n")
        summary_file.write(f"Detected OS: {detected_os}\n")
        summary_file.write(f"Open ports: {stats['open']}\n")
        summary_file.write(f"Closed ports: {stats['closed']}\n")
        summary_file.write(f"Filtered ports: {stats['filtered']}\n")
        summary_file.write(f"Skipped ports: {stats['skipped']}\n")
        summary_file.write(f"Errors: {stats['error']}\n")
        summary_file.write(f"Open-port list: {open_port_text}\n")


def log_results(
    logger: logging.Logger,
    target: str,
    results: Sequence[PortResult],
    services: Mapping[int, ServiceInfo],
    vulnerabilities: Mapping[int, Mapping[str, str]],
) -> None:
    for result in results:
        service = services.get(result.port, ServiceInfo())
        logger.info(
            "%s | port=%d | state=%s | service=%s | product=%s | version=%s",
            target,
            result.port,
            result.state,
            service.service,
            service.product,
            service.version,
        )
        for script_name, output in vulnerabilities.get(result.port, {}).items():
            logger.warning(
                "%s | port=%d | script=%s | output=%s",
                target,
                result.port,
                script_name,
                output.replace("\n", " "),
            )


def scan_target(
    target: str,
    ports: Sequence[int],
    scan_name: str,
    options: ScanOptions,
) -> None:
    logger, log_path = configure_logger(target)
    output_paths = create_output_paths(target)
    display_target_information(target)

    logger.info("Starting %s scan against %s", scan_name, target)
    results, elapsed = run_scan(
        target,
        ports,
        options.timeout,
        options.allow_reserved_ports,
        options.workers,
        options.mode,
    )
    open_ports = get_open_ports(results)

    services: Dict[int, ServiceInfo] = {}
    if options.service_detection:
        services = detect_services(target, open_ports)

    banners: Dict[int, str] = {}
    if options.banner_collection:
        banners = collect_banners(target, open_ports, options.workers)
        for port, banner in banners.items():
            services.setdefault(port, ServiceInfo()).banner = banner

    vulnerabilities: Dict[int, Dict[str, str]] = {}
    if options.vulnerability_scan:
        vulnerabilities = vulnerability_scan(target, open_ports)

    detected_os = detect_os(target) if options.os_detection else "Not requested"
    displayed_results = filter_results(results, options.filter_mode)
    if displayed_results:
        display_results(target, displayed_results, services)
    else:
        print(colourise(f"\nNo results matched '{options.filter_mode}'.", Colour.YELLOW))

    if options.banner_collection:
        display_banners(banners)
    if options.vulnerability_scan:
        display_vulnerabilities(vulnerabilities)

    stats = scan_statistics(results)
    display_statistics(stats)
    open_port_text = ", ".join(map(str, open_ports)) if open_ports else "None"
    print(f"\nElapsed time     : {elapsed:.2f} seconds")
    print(f"Ports scanned    : {len(results)}")
    print(f"Open port list   : {open_port_text}")
    print(f"Detected OS      : {detected_os}")
    print(f"Log file         : {log_path}")

    log_results(logger, target, results, services, vulnerabilities)
    logger.info("Elapsed time: %.2f seconds", elapsed)

    if options.export_csv:
        export_results_csv(output_paths["csv"], target, results, services, vulnerabilities)
        print(colourise(f"CSV exported to: {output_paths['csv']}", Colour.GREEN))
    if options.save_summary:
        save_summary(output_paths["summary"], target, stats, elapsed, open_ports, detected_os)
        print(colourise(f"Summary saved to: {output_paths['summary']}", Colour.GREEN))


def get_scan_options() -> ScanOptions:
    return ScanOptions(
        timeout=get_timeout(),
        workers=get_workers(),
        mode=get_execution_mode(),
        allow_reserved_ports=ask_yes_no("Allow scanning reserved ports (1-1023)?", default=True),
        filter_mode=get_filter_mode(),
        service_detection=ask_yes_no("Perform Nmap service/version detection?"),
        banner_collection=ask_yes_no("Attempt passive banner collection?"),
        vulnerability_scan=ask_yes_no("Run authorised Nmap vulnerability scripts?"),
        os_detection=ask_yes_no("Attempt Nmap OS detection?"),
        export_csv=ask_yes_no("Export CSV results?"),
        save_summary=ask_yes_no("Save scan summary?"),
    )


def display_configuration(targets: Sequence[str], ports: Sequence[int], scan_name: str, options: ScanOptions) -> None:
    mode_name = {"t": "Multithreading", "m": "Multiprocessing", "s": "Sequential"}[options.mode]
    print("\n" + "=" * 64)
    print("Scan Configuration")
    print("=" * 64)
    print(f"Targets              : {len(targets)}")
    print(f"Scan type            : {scan_name}")
    print(f"Ports requested      : {len(ports)}")
    print(f"Execution mode       : {mode_name}")
    print(f"Workers              : {options.workers}")
    print(f"Timeout              : {options.timeout:.2f}s")
    print(f"Result filter        : {options.filter_mode}")
    print(f"Service detection    : {options.service_detection}")
    print(f"Banner collection    : {options.banner_collection}")
    print(f"Vulnerability scan   : {options.vulnerability_scan}")
    print(f"OS detection         : {options.os_detection}")
    print(f"CSV export           : {options.export_csv}")
    print(f"Save summary         : {options.save_summary}")
    print("=" * 64)


def main() -> int:
    print_banner()
    targets = get_targets()
    ports, scan_name = get_scan_ports()
    if ports is None or scan_name is None:
        print("Exiting scanner.")
        return 0

    options = get_scan_options()
    display_configuration(targets, ports, scan_name, options)
    if not ask_yes_no("Start the scan?", default=True):
        print("Scan cancelled.")
        return 0

    overall_started = datetime.now()
    for target in targets:
        try:
            scan_target(target, ports, scan_name, options)
        except KeyboardInterrupt:
            print(colourise("\nScan interrupted by the user.", Colour.YELLOW))
            return 130
        except Exception as error:
            logging.exception("Unexpected error while scanning %s", target)
            print(colourise(f"Unexpected error while scanning {target}: {error}", Colour.RED))

    total_elapsed = (datetime.now() - overall_started).total_seconds()
    print("\n" + "=" * 64)
    print(f"All scans completed in {total_elapsed:.2f} seconds.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print(colourise("\nProgram stopped by the user.", Colour.YELLOW))
        raise SystemExit(130)
