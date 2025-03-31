import subprocess
import time
import re
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import dns.resolver
import dns.query
import dns.zone
import logging
import shutil
import platform
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ActiveSubdomainScanner")
logger.setLevel(logging.DEBUG)

ROOT_DIR = Path(__file__).parent
DICT_PATH = ROOT_DIR / "tools" / "wordlist.txt"
TEMP_DIR = ROOT_DIR / "temp"
MASSDNS_PATH = ROOT_DIR / "tools" / "massdns"

def get_massdns_path() -> Path:
    system = platform.system().lower()
    machine = platform.machine().lower()
    # 根据操作系统和架构生成massdns的名称
    name = f'massdns_{system}_{machine}'
    massdns_path = MASSDNS_PATH / name
    # 如果是windows系统，则将名称改为massdns.exe
    if system == 'windows':
        name = f'massdns.exe'
        massdns_path = MASSDNS_PATH / "windows" / name
    return massdns_path


'''使用了字典爆破、网页爬取、AXFR查询等方法，检测目标域名的子域名'''
class ActiveSubdomainScanner():
    def __init__(self, target_domain: str, enable_massdns: bool = True,
                 enable_axfr: bool = True, enable_html_crawling: bool = True):
        self.target_domain = target_domain
        self.enable_massdns = enable_massdns
        self.enable_axfr = enable_axfr
        self.enable_html_crawling = enable_html_crawling
        self.dict = []

    def gen_dict(self, domains=None):
        if not domains:
            try:
                with open(DICT_PATH, "r") as f:
                    domains = [f"{line.strip()}.{self.target_domain}" for line in f.readlines()]
                    self.dict = domains
                    logger.info(f"Dictionary loaded with {len(domains)} entries.")
            except FileNotFoundError:
                logger.error(f"Dictionary file '{DICT_PATH}' not found.")
                return None

        TEMP_DIR.mkdir(exist_ok=True)
        domains_path = TEMP_DIR / "temp_domains.txt"
        with open(domains_path, 'w') as outfile:
            for domain in domains:
                outfile.write(domain + '\n')
        return domains_path

    def is_subdomain(self, domain: str) -> bool:
        domain = domain.strip().lower()
        # 检查该域名是否以".目标域名"结尾，并确保它不与目标域名相同
        return domain.endswith("." + self.target_domain) and domain != self.target_domain

    # 使用massdns进行高效查询
    def massdns_resolve(self, domains_path: Path) -> Optional[Path]:
        massdns_path = get_massdns_path()
        resolver_path = MASSDNS_PATH /"lists" / "resolvers.txt"
        TEMP_DIR.mkdir(exist_ok=True)
        out_file = TEMP_DIR / "results.txt"
        if not massdns_path.exists():
            logger.error("MassDNS not found.")
            return None
        massdns_path.chmod(64)
        logger.info("Running MassDNS...")
        command = f"{massdns_path} --quiet -r {resolver_path} -t A -o S {domains_path} > {out_file}"
        subprocess.run(command, shell=True)
        return out_file

    def extract_domains_from_file(self, file_path: Path) -> set[str]:
        domains = set()
        with open(file_path, 'r') as file:
            for line in file:
                # 使用正则表达式提取域名
                match = re.match(r'([a-zA-Z0-9.-]+)\s+(A|CNAME)\s+', line)
                if match:
                    domain = match.group(1).rstrip('.')  # 去掉结尾的点
                    domains.add(domain)
        return domains

    def single_dns_resolve(self, domain: str) -> set[str]:
        found_domains = set()
        domains = self.check_dns_record(domain)
        found_domains.update(domains)
        return found_domains

    def check_dns_record(self, domain: str) -> set[str]:
        result = set()
        try:  # 查询A记录
            ip_list = [ip.to_text() for ip in dns.resolver.resolve(domain, "A")]
            if ip_list:
                result.add(domain)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers):
            pass
        try:  # 查询CNAME记录
            cname_list = [cname.to_text()[:-1] for cname in dns.resolver.resolve(domain, "CNAME")]
            result.update(cname_list)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers):
            pass
        try:  # 查询MX记录
            mx_list = [mx.to_text() for mx in dns.resolver.resolve(domain, "MX")]
            mx_list = [mx for mx in mx_list if self.is_subdomain(mx)]
            result.update(mx_list)
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers):
            pass
        return result

    # 使用线程池并行执行查询
    def parallel_brute_force(self, domains=None) -> set[str]:
        valid_domains = set()
        if not domains:
            domains = self.dict
        logger.info("Performing brute force without MassDNS, this may take a longer time...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            # 使用map函数将brute_force_subdomains函数并行执行
            results = executor.map(lambda sub: self.single_dns_resolve(sub), domains)
            for result in results:
                valid_domains.update(result)
        return valid_domains

    '''字典爆破'''
    def brute_force(self, domains=None) -> set[str]:
        if not domains:
            path = self.gen_dict()
            domains = self.dict
        else:
            path = self.gen_dict(domains)
        if not domains:
            logger.error("Brute force failed: No domains available to resolve.")
            return set()
        if self.enable_massdns:
            out_file = self.massdns_resolve(path)
            domains = self.extract_domains_from_file(out_file)
        else:
            domains = self.parallel_brute_force(domains)
        return domains

    def fetch_html(self, url: str):
        try:
            response = requests.get(url, timeout=5)
            return response.text
        except Exception:
            return ""

    '''爬取网站页面并提取子域名'''
    def extract_domains_from_html(self, domain: str) -> set[str]:
        regex = re.compile(r'https?://([a-zA-Z0-9-]+\.)*' + re.escape(self.target_domain))
        url = f"https://{domain}"
        html = self.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        new_domains = set()

        for link in soup.find_all('a', href=True):
            href = link['href']
            match = regex.match(href)
            if match:
                # 提取并保存子域名部分
                subdomain_match = match.group(1)  # 提取匹配到的子域名部分
                if subdomain_match:
                    new_domain = subdomain_match + self.target_domain
                    new_domains.add(new_domain)
        return new_domains

    def get_authoritative_ns(self):
        try:
            answers = dns.resolver.resolve(self.target_domain, 'NS')
            return [ns.to_text().rstrip('.') for ns in answers]
        except Exception as e:
            logger.warning(f"Failed to query NS records: {e}")
            return []

    def ns_axfr_query(self, nameserver: str) -> set[str]:
        try:
            logger.info(f"Attempting AXFR query on {nameserver}...")
            zone = dns.zone.from_xfr(dns.query.xfr(nameserver, self.target_domain))
            if zone is None:
                logger.warning(f"AXFR query failed: {nameserver} refused the request.")
                return set()

            found_domains = set()
            for name, node in zone.nodes.items():
                fqdn = name.to_text() + "." + self.target_domain
                found_domains.add(fqdn)
            return found_domains
        except Exception as e:
            logger.error(f"AXFR query failed: {e}")
            return set()

    '''AXFR查询'''
    def axfr_query(self) -> set[str]:
        domains = set()
        nameservers = self.get_authoritative_ns()
        for nameserver in nameservers:
            found_domains = self.ns_axfr_query(nameserver)
            domains.update(found_domains)
        return domains


    def __call__(self):
        time1 = time.time()
        valid_domains = self.brute_force()
        time2 = time.time()
        logger.info(f"Brute-force completed in {time2 - time1:.2f} seconds, found {len(valid_domains)} valid subdomains.")
        if self.enable_axfr:
            valid_domains.update(self.axfr_query())
            time3 = time.time()
            logger.info(f"AXFR query completed in {time3 - time2:.2f} seconds.")

        if self.enable_html_crawling:
            time3 = time.time()
            logger.info("Starting HTML crawling...")
            new_domains = valid_domains.copy()
            crawled_domains = set()
            with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
                while new_domains:
                    temp = new_domains.copy()
                    new_domains.clear()
                    # 使用executor.map来并行执行 extract_subdomains
                    futures = {executor.submit(self.extract_domains_from_html, domain): domain for domain in temp}
                    # 等待所有任务完成，并将新提取的子域名添加到 new_domains 中
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future_domains = future.result()
                            new_domains.update(future_domains - crawled_domains - valid_domains)
                        except Exception as e:
                            logger.error(f"Error extracting subdomains for {futures[future]}: {e}")
                    crawled_domains.update(new_domains)
            crawled_domains = {domain for domain in crawled_domains if self.is_subdomain(domain)}
            crawled_domains = self.brute_force(crawled_domains)
            valid_domains.update(crawled_domains)
            time4 = time.time()
            logger.info(
                f"HTML extraction completed in {time4 - time3:.2f} seconds, "
                f"found {len(crawled_domains)} additional valid subdomains."
            )

        end_time = time.time()
        logger.info(
            f"Active subdomain scan completed: "
            f"{len(valid_domains)} valid subdomains discovered in {end_time - time1:.2f} seconds."
        )
        shutil.rmtree(TEMP_DIR)
        return valid_domains


if __name__ == "__main__":
    scanner = ActiveSubdomainScanner("sjtu.edu.cn", True, True)
    domains = scanner()
