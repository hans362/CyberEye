import socket
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
import nmap
import requests


def get_http_header(host, port):
    """发送 HTTP 请求并返回响应头"""
    try:
        # 创建一个 socket 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # 如果是 HTTPS，使用 SSL 包装 socket
        if port == 443:
            context = ssl.create_default_context()
            context.check_hostname = False  # 禁用主机名检查
            context.verify_mode = ssl.CERT_NONE  # 禁用证书验证
            sock = context.wrap_socket(sock, server_hostname=host)

        # 连接到目标主机和端口
        sock.connect((host, port))

        # 构造 HTTP 请求
        #request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        request = (
            "GET / HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
            "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
            "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8\r\n"
            "Accept-Encoding: gzip, deflate, br\r\n"  # 允许压缩响应
            "Connection: close\r\n\r\n"
        )
        sock.sendall(request.encode())

        # 接收响应
        response = b""
        while True:
            data = sock.recv(1024)
            if not data:
                break
            response += data

        # 关闭连接
        sock.close()

        # 解码响应并获取头部信息
        response = response.decode('utf-8', errors='ignore')
        headers = response.split("\r\n\r\n")[0]  # 获取 HTTP 头部部分
        
        return headers

    except Exception as e:
        return f"错误: {str(e)}"

def get_ssh_banner(host, port=22):
    """获取 SSH 端口的 Banner 信息"""
    try:
        # 创建 socket 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # 连接到目标端口
        sock.connect((host, port))

        # 读取 SSH Banner
        banner = sock.recv(1024).decode('utf-8', errors='ignore')

        # 关闭连接
        sock.close()

        if banner.startswith("SSH-"):
            return banner.strip()
        return "无法识别的 SSH 服务"

    except Exception as e:
        return f"无法获取 SSH 信息: {str(e)}"

def scan_port_with_nmap(host, port):
    """使用 nmap 获取端口服务信息"""
    nm = nmap.PortScanner()
    nm.scan(host, str(port), arguments='-sV --script ssl-enum-ciphers')

    for host in nm.all_hosts():
        if port in nm[host]["tcp"]:
            state = nm[host]["tcp"][port]["state"]
            if state == "open":
                service = nm[host]["tcp"][port]["name"]
                version_info = nm[host]["tcp"][port].get("version", "")
                return f"{service} {version_info}".strip()
    return "Unknown"


def service_scan_http(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    """扫描 HTTP 端口"""
    results = []
    for port in ports:
        if port in [80, 8080]:
            banner = get_http_header(ip, port)
            results.append({"port": port, "banner": banner, "protocol": "HTTP"})
    return results


def service_scan_https(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    """扫描 HTTPS 端口"""
    results = []
    if 443 in ports:
        banner = get_http_header(ip, 443)
        results.append({"port": 443, "banner": banner, "protocol": "HTTPS"})
    return results


def service_scan_ssh(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    """扫描 SSH 端口"""
    results = []
    if 22 in ports:
        banner = get_ssh_banner(ip, 22)
        results.append({"port": 22, "banner": banner, "protocol": "SSH"})
    return results


def service_scan(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    """主扫描函数，调用 HTTP/HTTPS/SSH 端口扫描"""
    results = (
        service_scan_http(ip, ports)
        + service_scan_https(ip, ports)
        + service_scan_ssh(ip, ports)
    )

    # 多线程扫描其余端口
    def scan_other_port(port):
        """扫描其他非 HTTP/HTTPS/SSH 的端口"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            banner = scan_port_with_nmap(ip, port)
            protocol = banner.split()[0].upper() if banner != "Unknown" else "UNKNOWN"
            return {"port": port, "banner": banner, "protocol": protocol}
        return None

    other_ports = [
        port for port in ports if port not in [22, 80, 443, 8080]
    ]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scan_other_port, port) for port in other_ports]
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results
