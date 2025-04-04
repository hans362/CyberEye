import requests
import time
import logging
import concurrent.futures
from pathlib import Path
import socket

from config import VT_API_KEY, DNSDUMPSTER_API_KEY

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PassiveSubdomainScanner")
logger.setLevel(logging.DEBUG)

ROOT_DIR = Path(__file__).parent
TEMP_DIR = ROOT_DIR / "temp"

'''共有三种被动子域名查询方式：VirusTotal、Crtsh、DNSdumpster，并通过DNS解析验证域名是否有效'''
'''使用前需于config.py中填写apikey'''

class VirusTotalAPI:
    def __init__(self, domain: str):
        self.domain = domain
        self.base_url = 'https://www.virustotal.com/api/v3/domains/'
        self.subdomains = set()

    def get_header(self):
        vt_api_key = VT_API_KEY
        return {'x-apikey': vt_api_key}

    def get_subdomains(self):
        next_cursor = ''
        while True:
            headers = self.get_header()
            params = {'limit': '40', 'cursor': next_cursor} if next_cursor else {'limit': '40'}
            url = f'{self.base_url}{self.domain}/subdomains'
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                logger.warning(f"Error: {response.status_code} - {response.text}")
                break

            data = response.json()

            subdomains = [item['id'] for item in data.get('data', [])]
            if not subdomains:
                break

            self.subdomains.update(subdomains)

            # 处理分页游标
            meta_data = data.get('meta', {})
            next_cursor = meta_data.get('cursor', None)

            if not next_cursor:
                break

    def get_subdomains_list(self):
        return list(self.subdomains)

class CrtshQuery:
    def __init__(self, domain: str):
        self.domain = domain
        self.url = 'https://crt.sh/'
        self.subdomains = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }

    def fetch(self):
        params = {'q': f'%.{self.domain}', 'output': 'json'}
        try:
            response = requests.get(self.url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f'[!] CrtshQuery Status code error: {response.status_code}')
        except requests.exceptions.Timeout:
            logger.warning('[!] CrtshQuery Request timed out, please try again later.')
        except Exception as e:
            logger.error(f'[!] CrtshQuery Request error: {e}')
        return []

    def extract_subdomains(self, data):
        for entry in data:
            name_value = entry.get('name_value', '')
            domains = name_value.split('\n')
            for d in domains:
                d = d.strip().lower()
                if self.domain in d:
                    self.subdomains.add(d)

    def get_subdomains(self):
        data = self.fetch()
        if not data:
            return []
        self.extract_subdomains(data)
        return list(self.subdomains)

class DNSdumpsterAPI:
    def __init__(self, domain: str):
        self.domain = domain
        self.url = f"https://api.dnsdumpster.com/domain/{self.domain}"
        self.subdomains = set()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }

    def fetch(self):
        dnsdumpster_api_key = DNSDUMPSTER_API_KEY
        headers = {**self.headers, "X-API-Key": dnsdumpster_api_key}
        try:
            response = requests.get(self.url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f'[!] DNSdumpster Status code error: {response.status_code}')
        except requests.exceptions.Timeout:
            logger.warning('[!] DNSdumpster request timed out, please try again later.')
        except Exception as e:
            logger.error(f'[!] DNSdumpster request error: {e}')
        return []

    def extract_subdomains(self, data):
        if 'a' in data:
            for record in data['a']:
                host = record.get("host")
                if host and host != self.domain:
                    self.subdomains.add(host)
        if 'cname' in data:
            for record in data['cname']:
                host = record.get("host")
                if host and host != self.domain:
                    self.subdomains.add(host)

    def get_subdomains(self):
        data = self.fetch()
        if data:
            self.extract_subdomains(data)
        return list(self.subdomains)

class PassiveSubdomainScanner:
    def __init__(self, target_domain: str, enable_crtsh: bool = True, enable_dnsdumpster: bool = True):
        self.target_domain = target_domain
        self.enable_crtsh = enable_crtsh
        self.enable_dnsdumpster = enable_dnsdumpster
        self.subdomains = set()

    def get_subdomains_from_crtsh(self):
        if self.enable_crtsh:
            crtsh_scanner = CrtshQuery(self.target_domain)
            crtsh_subdomains = crtsh_scanner.get_subdomains()
            self.subdomains.update(crtsh_subdomains)

    def get_subdomains_from_dnsdumpster(self):
        if self.enable_dnsdumpster:
            dnsdumpster_scanner = DNSdumpsterAPI(self.target_domain)
            dnsdumpster_subdomains = dnsdumpster_scanner.get_subdomains()
            self.subdomains.update(dnsdumpster_subdomains)

    def get_subdomains_from_virustotal(self):
        vt_api = VirusTotalAPI(self.target_domain)
        vt_api.get_subdomains()
        virustotal_subdomains = vt_api.get_subdomains_list()
        self.subdomains.update(virustotal_subdomains)

    def is_valid_domain(self, domain: str) -> bool:
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False

    def validate_subdomains(self, subdomains: list) -> list:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            valid_subdomains = list(executor.map(self.is_valid_domain, subdomains))
        # 过滤掉无效的子域名
        return [subdomain for subdomain, valid in zip(subdomains, valid_subdomains) if valid]

    def __call__(self):
        if not isinstance(self.target_domain, str):
            logger.error(f"Target domain must be a string, got {type(self.target_domain)}")
            return set()
        self.target_domain = self.target_domain.strip()

        start_time = time.time()
        # 收集子域名
        self.get_subdomains_from_crtsh()
        self.get_subdomains_from_dnsdumpster()
        self.get_subdomains_from_virustotal()

        # 验证子域名
        valid_subdomains = self.validate_subdomains(list(self.subdomains))

        end_time = time.time()
        logger.info(f"Passive subdomain scan completed: "
                    f"{len(valid_subdomains)} valid subdomains discovered in {end_time - start_time:.2f} seconds.")
        return valid_subdomains


if __name__ == "__main__":
    scanner = PassiveSubdomainScanner("fudan.edu.cn")
    subdomains = scanner()

    # 输出结果
    logger.info(f"Found {len(subdomains)} valid subdomains:")
    for subdomain in subdomains:
        print(subdomain)