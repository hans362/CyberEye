import os
from .subdomain_scanner import ActiveSubdomainScanner
import socket
from concurrent.futures import ThreadPoolExecutor


def subdomain_collect_method1(domain: str) -> list[str]:
    # return ["aaa." + domain]
    scanner = ActiveSubdomainScanner(domain)
    return list(scanner())


def subdomain_collect_method2(domain: str) -> list[str]:
    return ["bbb." + domain]


def subdomain_collect_method3(domain: str) -> list[str]:
    return ["ccc." + domain]


def subdomain_collect(domain: str) -> list[str]:
    return list(
        set(
            subdomain_collect_method1(domain)
            + subdomain_collect_method2(domain)
            + subdomain_collect_method3(domain)
        )
    )


def get_ip_addr(domain: str) -> list[str]:
    try:
        ips = socket.getaddrinfo(domain, None)
        return sorted(list(set([ip[4][0] for ip in ips])))
    except Exception:
        return []


def ip_resolve(domains: list[str]) -> dict[str, list[str]]:
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        results = list(executor.map(get_ip_addr, domains))
    return {domain: ips for domain, ips in zip(domains, results)}


if __name__ == "__main__":
    print(subdomain_collect("example.com"))
