import os
from .activesubdomainscanner import ActiveSubdomainScanner
from .passivesubdomainscanner import PassiveSubdomainScanner
import socket
from concurrent.futures import ThreadPoolExecutor


def active_subdomain_collect(domain: str) -> list[str]:
    scanner = ActiveSubdomainScanner(domain)
    return list(scanner())

def passive_subdomain_collect(domain: str) -> list[str]:
    scanner = PassiveSubdomainScanner(domain)
    return list(scanner())

def subdomain_collect(domain: str) -> list[str]:
    with ThreadPoolExecutor() as executor:
        # 并行运行 active_subdomain_collect 和 passive_subdomain_collect
        future_active = executor.submit(active_subdomain_collect, domain)
        future_passive = executor.submit(passive_subdomain_collect, domain)

        # 获取结果
        active_subdomains = future_active.result()
        passive_subdomains = future_passive.result()

    # 合并去重
    all_subdomains = set(active_subdomains + passive_subdomains)
    return list(all_subdomains)


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
    print(subdomain_collect("sjtu.cn"))
