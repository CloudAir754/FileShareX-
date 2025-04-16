# 文件分享系统

一个基于Flask的轻量级文件分享系统，支持文件上传、提取码分享和下载管理，包含管理员后台功能。可以直接在Python运行，亦可使用Docker-Compose构建。

## 功能特性

- **文件上传与分享**：支持多种文件类型上传，生成唯一提取码
- **安全控制**：支持设置有效期、最大下载次数
- **管理员后台**：文件管理、系统监控
- **安全防护**：速率限制、密码爆破防护、下载频率控制
- **多文件类型支持**：图片、文档、压缩包、音视频等

## 安装与运行-Python直接运行

### 依赖安装

```bash
pip install -r ./app/requirements.txt
```

### 运行方式

```bash
# 基本运行
python ./app/app.py

# 自定义参数运行（可选）
python app.py --host 0.0.0.0 --port 5000 --admin-password yourpassword --clear-on-startup

# 后台运行
nohup python .app/app.py > output.log 2>&1 &
```

### 命令行参数

| 参数 | 说明 |
|------|------|
| `--host` | 绑定主机地址 (默认: 0.0.0.0) |
| `--port` | 绑定端口号 (默认: 5000) |
| `--admin-password` | 设置管理员密码 |
| `--clear-on-startup` | 启动时清空数据库和上传文件夹 |


## 安装与运行-DockerCompose运行
在根目录下运行（需要安装好Docker和Docker-compose）


```
# 构建并启动服务
docker-compose up -d --build
## 无需缓存的从头构建
docker-compose up -d --build --no-cache
```

### 其他运维命令
```
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止并删除旧容器
docker-compose down

# 启动服务
docker-compose up -d
docker-compose start 
docker-compose stop 
docker-compose restart 

# 传给远程主机（自用）
tar -czvf FileShareX.tar.gz FileShareX/
scp FileShareX.tar.gz user@Aim_ip:~/downloads/
tar -xzvf FileShareX.gz
```


## 配置说明

编辑 `config.py` 文件修改系统配置，主要配置项包括：

- `SECRET_KEY`: Flask应用密钥
- `UPLOAD_FOLDER`: 文件上传目录
- `ALLOWED_EXTENSIONS`: 允许上传的文件类型
- `ADMIN_PASSWORD`: 管理员密码
- 各种安全限制参数



## 系统维护

### 数据库清理

```bash
flask cleanup
```

此命令会：
1. 删除所有过期文件记录和对应的物理文件
2. 清理30天前的下载记录

### 管理员功能

访问 `/admin/login` 使用管理员密码登录后可以：

- 查看/搜索所有文件
- 上传新文件
- 删除/禁用文件
- 查看系统统计信息

## 安全特性

1. **速率限制**：
   - 首页访问：10次/分钟
   - 下载请求：3次/分钟
   - 管理员接口：5次/分钟

2. **密码爆破防护**：
   - 5分钟内最多尝试2次提取码
   - 失败后IP会被暂时封锁

3. **下载频率控制**：
   - 同一IP在5分钟内对同一文件最多下载3次

4. **管理员登录保护**：
   - 失败延迟响应
   - 尝试次数限制
   - 会话超时

## 文件类型支持

系统默认支持以下文件类型：

| 类别 | 扩展名 |
|------|------|
| 图片 | jpg, jpeg, png, gif, bmp, webp |
| 文档 | pdf, doc, docx, xls, xlsx, ppt, pptx, txt |
| 压缩包 | zip, rar, 7z, tar, gz |
| 音频 | mp3, wav, ogg, flac |
| 视频 | mp4, avi, mov, mkv, flv |

## 错误处理

系统提供友好的错误页面：

- 400/401/403/404 错误
- 413 文件过大错误
- 429 请求过多
- 500 服务器错误


## 项目结构

```
FileShareX
    ├── app
    │   ├── app.py            # 主应用文件
    │   ├── config.py         # 配置文件
    │   ├── models.py         # 数据库模型
    │   ├── requirements.txt  # 依赖列表
    │   ├── static            # 静态文件
    │   └── templates         # 模板文件
    ├── docker-compose.yml    # docker配置
    ├── Dockerfile            # Flask配置
    ├── nginx
    │   └── nginx.conf        # Nginx 配置
    └── README.md             # 自述文件
```

## 注意事项

1. 生产环境应修改 `SECRET_KEY` 和 `ADMIN_PASSWORD`
2. 建议启用 `SESSION_COOKIE_SECURE` (HTTPS环境下)
3. 文件存储在本地，需要考虑磁盘空间
4. 默认配置适合小型应用，高并发环境需要调整限制参数
5. 部分代码由AI开发；平台包括：Deepseek V3（官网）、Deepseek V3（腾讯元宝）
