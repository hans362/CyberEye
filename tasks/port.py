import ipaddress
import os
import socket
from scapy.all import TCP, IP, sr1, RandShort, IPv6
from concurrent.futures import ThreadPoolExecutor

from config import PORT_SCAN_RANGE, PORT_SCAN_TIMEOUT


def check_permission():
    if os.name == "nt":
        import ctypes

        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            return False
    elif os.name == "posix":
        if os.getuid() == 0:
            return True
        else:
            return False
    else:
        return False


def tcp_connect_scan(ip, port):
    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.version == 6:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(PORT_SCAN_TIMEOUT)
    response = s.connect_ex((ip, port))
    s.close()
    if response == 0:
        return True
    return False


def tcp_syn_scan(ip, port):
    sport = RandShort()
    ip_obj = ipaddress.ip_address(ip)
    if ip_obj.version == 6:
        response = sr1(
            IPv6(dst=ip) / TCP(sport=sport, dport=port, flags="S"),
            timeout=PORT_SCAN_TIMEOUT,
            verbose=False,
        )
    else:
        response = sr1(
            IP(dst=ip) / TCP(sport=sport, dport=port, flags="S"),
            timeout=PORT_SCAN_TIMEOUT,
            verbose=False,
        )
    if response:
        if response.haslayer(TCP):
            flags = response.getlayer(TCP).flags
            if "S" in flags and "A" in flags:
                return True
    return False


def port_scan(ip: str) -> list[int]:
    print(f"[PortScan] Scanning {ip}...")
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(
            executor.map(tcp_connect_scan, [ip] * len(PORT_SCAN_RANGE), PORT_SCAN_RANGE)
        )
    open_ports = set([port for port, result in zip(PORT_SCAN_RANGE, results) if result])
    # TCP SYN scan requires root privileges, so run it only if permission is granted
    if check_permission():
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            results = list(
                executor.map(tcp_syn_scan, [ip] * len(PORT_SCAN_RANGE), PORT_SCAN_RANGE)
            )
        open_ports.update(
            set([port for port, result in zip(PORT_SCAN_RANGE, results) if result])
        )
    print(f"[PortScan] Scan completed for {ip}.")
    return sorted(list(open_ports))


if __name__ == "__main__":
    pass
