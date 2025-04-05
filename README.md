# CyberEye

一款网络空间测绘工具

## ✨ 概述

随着数字化转型加速，企业网络资产数量快速增长，暴露在互联网上的资产面不断扩大。传统人工资产盘点方式效率低下，无法应对快速变化的网络环境。网络攻击者经常利用未被发现的子域名、过期未下线的云服务等“影子资产”作为攻击入口。

CyberEye 旨在通过自动化测绘技术，为网络安全从业者提供高效、全面的互联网资产发现与测绘能力，帮助用户构建完整的网络空间资产图谱，从而支撑安全风险评估、攻击面管理和资产合规性审计等关键业务场景。

## 🚀 部署

### ⚙️ 裸机部署

#### 前置要求

- Python 3.12
- `pip` 包管理器
- MySQL 8
- 具备访问 PyPI 或其镜像的网络连接条件

若希望系统在端口扫描阶段使用 TCP SYN 扫描方式进行半开放式扫描，则部分组件需要以 Root 权限运行。

#### 部署 Web 服务端

1. 新建 Python 虚拟环境。
2. 在源码目录下执行以下命令安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 修改 `config.py` 中的配置，或新建 `.env` 文件使用环境变量进行配置，避免直接修改代码。
4. 在源码目录下执行以下命令启动 Web 服务端：
   ```bash
   fastapi run
   ```
   系统将监听 8000 端口。如需修改运行参数，请参考 FastAPI 官方文档。测试成功启动后，使用 `Ctrl-C` 中止。
5. 在源码目录下执行以下命令创建第一个管理员用户：
   ```bash
   python3 manage.py create_admin
   ```
   请务必使用强密码。
6. 参考 Supervisor 或 Systemd 官方文档，实现持久化运行和自动重启。

#### 部署调度器

1. 激活 Python 虚拟环境。
2. 在源码目录下运行以下命令启动调度器：
   ```bash
   python3 scheduler.py
   ```
   若无任何输出，则说明调度器运行正常。测试成功启动后，使用 `Ctrl-C` 中止。
3. 参考 Supervisor 或 Systemd 官方文档，实现持久化运行和自动重启。

**警告**：与任务处理器不同，必须保证有且仅有 1 个调度器在运行。同时运行多个调度器不仅没有加速作用，反而可能导致系统调度异常（如出现重复的任务）。

#### 部署任务处理器

1. 激活 Python 虚拟环境。
2. 在源码目录下运行以下命令启动任务处理器：
   ```bash
   python3 worker.py
   ```
   若无任何输出，则说明任务处理器运行正常。测试成功启动后，使用 `Ctrl-C` 中止。
3. 参考 Supervisor 或 Systemd 官方文档，实现持久化运行和自动重启。
4. **建议**：参考 Supervisor 或 Systemd 官方文档，部署多个同时运行的任务处理器，以实现并行加速。

**注意**：若希望系统在端口扫描阶段使用 TCP SYN 扫描方式进行半开放式扫描，请使用 Root 权限运行任务处理器。否则，系统将自动回落至 TCP Connect 扫描方式。对于 Web 服务端和调度器，无需 Root 权限。

### 🐋 容器化部署

#### 前置要求

- Docker
- Docker Compose
- 具备访问 DockerHub 或其镜像、PyPI 或其镜像的网络连接条件

#### 部署所有组件

1. 按需修改源码目录下的 `docker-compose.yml`，配置挂载点及监听端口，按需修改环境变量。
2. 在源码目录下执行以下命令启动所有组件：
   ```bash
   docker-compose up -d
   ```
3. 在源码目录下执行以下命令创建第一个管理员用户：
   ```bash
   docker-compose exec app python3 manage.py create_admin
   ```
   请务必使用强密码。

## 🔧 配置

以下为系统各配置项的说明及默认值：

| 配置项                        | 说明                      | 默认值                  | 环境变量                      |
| ----------------------------- | ------------------------- | ----------------------- | ----------------------------- |
| `DATABASE_HOST`               | 数据库主机地址            | `localhost`             | `DATABASE_HOST`               |
| `DATABASE_PORT`               | 数据库端口                | `3306`                  | `DATABASE_PORT`               |
| `DATABASE_USER`               | 数据库用户名              | `root`                  | `DATABASE_USER`               |
| `DATABASE_PASSWORD`           | 数据库密码                | `root`                  | `DATABASE_PASSWORD`           |
| `DATABASE_NAME`               | 数据库名称                | `cybereye`              | `DATABASE_NAME`               |
| `GEOIP_DATABASES_AUTO_UPDATE` | 是否自动更新 GeoIP 数据库 | `False`                 | `GEOIP_DATABASES_AUTO_UPDATE` |
| `PORT_SCAN_RANGE`             | 端口扫描范围              | `[21, 22, ..., 27017]`  | 无                            |
| `PORT_SCAN_TIMEOUT`           | 端口扫描超时时间（秒）    | `1`                     | `PORT_SCAN_TIMEOUT`           |
| `SERVICE_SCAN_KEYWORDS`       | 服务扫描关键字            | `{ "SSH": "SSH", ... }` | 无                            |
| `SERVICE_SCAN_TIMEOUT`        | 服务扫描超时时间（秒）    | `2`                     | `SERVICE_SCAN_TIMEOUT`        |
| `SCHEDULER_INTERVAL`          | 调度器间隔时间（秒）      | `2`                     | `SCHEDULER_INTERVAL`          |
| `WORKER_INTERVAL`             | 任务处理器间隔时间（秒）  | `0.2`                   | `WORKER_INTERVAL`             |
| `VT_API_KEY`                  | VirusTotal API KEY        | 空                      | `VT_API_KEY`                  |
| `DNSDUMPSTER_API_KEY`         | DNSDumpster API KEY       | 空                      | `DNSDUMPSTER_API_KEY`         |

## 🛠️ 开发

请参考 [⚙️ 裸机部署](#️-裸机部署) 部分，完成系统的本地部署。开发过程中可使用 `fastapi dev` 开启热更新，在代码发生变更时无需手动重启 Web 服务端。

## ❤️ 致谢

系统使用了以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Vue](https://vuejs.org/)
- [MassDNS](https://github.com/blechschmidt/massdns)
- [scapy](https://scapy.readthedocs.io/en/latest/)
- [GeoIP2](https://geoip2.readthedocs.io/en/latest/)