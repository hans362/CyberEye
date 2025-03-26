def service_scan_http(ip: str, ports: list[int]) -> dict[int, str]:
    return {80: "HTTP/1.1 200 OK"}


def service_scan_https(ip: str, ports: list[int]) -> dict[int, str]:
    return {443: "HTTP/1.1 200 OK"}


def service_scan_ssh(ip: str, ports: list[int]) -> dict[int, str]:
    return {22: "SSH-2.0-OpenSSH_7.9p1 Debian-10+deb10u2"}


def service_scan(ips: list[str], ports: list[int]) -> dict[str, dict[int, str]]:
    return {
        
    }
