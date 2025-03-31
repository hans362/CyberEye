from .subdomain_scanner import ActiveSubdomainScanner

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


def ip_resolve(domain: str) -> list[str]:
    return ["127.0.0.1", "12.34.56.78"]


if __name__ == "__main__":
    print(subdomain_collect("example.com"))