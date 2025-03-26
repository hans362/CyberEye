def service_scan_http(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    return [
        {"port": 80, "banner": "HTTP/1.1 200 OK", "protocol": "HTTP"},
        {"port": 8080, "banner": "HTTP/1.1 200 OK", "protocol": "HTTP"},
    ]


def service_scan_https(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    return [{"port": 443, "banner": "HTTP/1.1 200 OK", "protocol": "HTTPS"}]


def service_scan_ssh(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    return [{"port": 22, "banner": "SSH-2.0-OpenSSH_7.9", "protocol": "SSH"}]


def service_scan(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    return list(
        service_scan_http(ip, ports)
        + service_scan_https(ip, ports)
        + service_scan_ssh(ip, ports)
    )
