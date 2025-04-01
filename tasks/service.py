import os
import socket
import ssl
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from config import SERVICE_SCAN_TIMEOUT


def detect_service(banner: str) -> str:
    service_keywords = {
        "SSH-": "SSH",
        "220": "SMTP",
        "220-": "FTP",
        "MySQL": "MySQL",
        "PostgreSQL": "PostgreSQL",
        "Redis": "Redis",
        "Elasticsearch": "Elasticsearch",
        "Memcached": "Memcached",
        "MongoDB": "MongoDB",
        "IMAP": "IMAP",
        "POP3": "POP3",
        "SMB": "SMB",
        "VNC": "VNC",
        "RDP": "RDP",
        "LDAP": "LDAP",
    }
    for keyword, service in service_keywords.items():
        if keyword in banner:
            return service
    return "未知"


def http_scan(ip: str, port: int) -> dict[str, int | str] | None:
    try:
        if ipaddress.ip_address(ip).version == 6:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SERVICE_SCAN_TIMEOUT)
        s.connect((ip, port))
        request = f"GET / HTTP/1.1\r\nHost: {ip}:{port}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())
        response = s.recv(1024)
        s.close()
        response = response.decode("utf-8", errors="ignore")
        if "HTTP" in response:
            return {
                "port": port,
                "banner": response,
                "protocol": "HTTP",
            }
        return None
    except Exception:
        return None


def https_scan(ip: str, port: int) -> dict[str, int | str] | None:
    try:
        if ipaddress.ip_address(ip).version == 6:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SERVICE_SCAN_TIMEOUT)
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        s = context.wrap_socket(s, server_hostname=ip)
        s.connect((ip, port))
        request = f"GET / HTTP/1.1\r\nHost: {ip}:{port}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())
        response = s.recv(1024)
        s.close()
        response = response.decode("utf-8", errors="ignore")
        if "HTTP" in response:
            return {
                "port": port,
                "banner": response,
                "protocol": "HTTPS",
            }
        return None
    except Exception:
        return None


def other_scan(ip: str, port: int) -> dict[str, int | str] | None:
    try:
        if ipaddress.ip_address(ip).version == 6:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(SERVICE_SCAN_TIMEOUT)
        s.connect((ip, port))
        banner = s.recv(1024).decode("utf-8", errors="ignore")
        s.close()
        return {
            "port": port,
            "banner": banner,
            "protocol": detect_service(banner),
        }
    except Exception:
        return None


def single_port_service_scan(ip: str, port: int) -> dict[str, int | str]:
    # 尝试 HTTPS 扫描
    result = https_scan(ip, port)
    if result:
        return result
    # 尝试 HTTP 扫描
    result = http_scan(ip, port)
    if result:
        return result
    # 其他协议扫描
    result = other_scan(ip, port)
    if result:
        return result
    return {
        "port": port,
        "banner": "",
        "protocol": "未知",
    }


def service_scan(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(single_port_service_scan, [ip] * len(ports), ports))
    return results
