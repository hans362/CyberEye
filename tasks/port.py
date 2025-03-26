def port_scan_method1(ip: str) -> list[int]:
    return [80, 443]


def port_scan_method2(ip: str) -> list[int]:
    return [8080, 8443]


def port_scan_method3(ip: str) -> list[int]:
    return [21, 22]


def port_scan(ip: str) -> list[int]:
    return list(
        set(port_scan_method1(ip) + port_scan_method2(ip) + port_scan_method3(ip))
    )
