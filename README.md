
### 运行步骤

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **数据库创建用户**

```bash
python manage.py create_admin
```

3. **运营网站**

```bash
fastapi run
```

4. **其他依赖文件**

```bash
python scheduler.py
python worker.py
```