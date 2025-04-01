import socket
import ssl

common_ports = [21, 22, 23, 25, 53, 80, 81, 110, 135, 139, 443, 445, 1433, 1521, 3306, 5432, 6379, 7001, 8000, 8080, 8089, 9000, 9200, 11211, 27017]

common_services = {
    21: "FTP (File Transfer Protocol)",
    22: "SSH (Secure Shell)",
    23: "Telnet",
    25: "SMTP (Simple Mail Transfer Protocol)",
    53: "DNS (Domain Name System)",
    80: "HTTP (Hypertext Transfer Protocol)",
    110: "POP3 (Post Office Protocol)",
    143: "IMAP (Internet Message Access Protocol)",
    443: "HTTPS (HTTP Secure)",
    3306: "MySQL Database",
    5432: "PostgreSQL Database",
    6379: "Redis",
    9200: "Elasticsearch",
    11211: "Memcached",
    27017: "MongoDB",
}

def socket_get_banner(host, port):
    """获取指定端口的 Banner 信息"""
    try:
        # 创建 socket 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        # 连接到目标主机和端口
        sock.connect((host, port))

        # 接收数据
        banner = sock.recv(1024).decode('utf-8', errors='ignore')

        # 关闭连接
        sock.close()

        return banner.strip()

    except Exception as e:
        return f"错误: {str(e)}"

def scan_service_banner(ip: str, port: int) -> dict[str, str]:
    # 扫描指定 IP 地址的端口并返回服务和 Banner 信息
    service_banner = socket_get_banner(ip, port)

    if not service_banner:
        return "未知", ""

    # 匹配常见服务
    service = "未知"
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

    # 关键字匹配服务
    for keyword, srv in service_keywords.items():
        if keyword in service_banner:
            service = srv
            break

    return service, service_banner

def get_http_header(host, port):
    """发送 HTTP 请求并返回响应头"""
    try:
        # 创建一个 socket 连接
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(20)

        context = ssl.create_default_context()
        context.check_hostname = False  # 禁用主机名检查
        context.verify_mode = ssl.CERT_NONE  # 禁用证书验证
        sock = context.wrap_socket(sock, server_hostname=host)

        # 连接到目标主机和端口
        sock.connect((host, port))

        # 构造 HTTPS 请求
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
        
        return ("HTTPS", headers)

    except Exception as e:
        """发送 HTTP 请求并返回响应头"""
        try:
            # 创建一个 socket 连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(20)

            sock.connect((host, port))
 
            request = f"GET / HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            
            sock.sendall(request.encode())

            response = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response += data

            sock.close()

            response = response.decode('utf-8', errors='ignore')
            headers = response.split("\r\n\r\n")[0]  # 获取 HTTP 头部部分
            
            return ("HTTP", headers)

        except Exception as e:
            return ("未知", str(e))

def scan_port(host, port):
    """扫描单个端口"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    result = sock.connect_ex((host, port))

    if result == 0:
        # 获取端口服务名称和额外信息
        service = None
        additional_info = None
        if not service:
            service, additional_info = scan_service_banner(host, port)
            if service == "未知" or additional_info == "" or additional_info == None:
                # 尝试使用 HTTPS 请求获取更多信息
                service, additional_info = get_http_header(host, port)
                # 仍获取不到服务名称，则说明不在我们探测的常用服务类型中
                if not service:
                    service = "未知"
            
        return port, additional_info, service
    
    sock.close()
    return None

def service_scan(ip: str, ports: list[int]) -> list[dict[str, int | str]]:
    results = []
    for port in ports:
        result = scan_port(ip, port)
        if result:
            port, banner, protocol = result
            results.append(
                {
                    "port": port,
                    "banner": banner[:1000],
                    "protocol": protocol,
                }
            )
    return results
