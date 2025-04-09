import os
from datetime import timedelta

class Config:
    SECRET_KEY =  '12345'
    UPLOAD_FOLDER = 'files'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx', 'xls', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    DEFAULT_EXPIRE_DAYS = 7  # 默认7天后过期
    CODE_LENGTH = 6  # 提取码长度
    CLEAR_ON_STARTUP = True
    # 速率限制配置
    RATE_LIMIT_DEFAULT = "200 per day, 50 per hour"  # 全局默认限制
    RATE_LIMIT_INDEX = "10 per minute"  # 首页/提取码尝试限制
    RATE_LIMIT_DOWNLOAD = "3 per minute"  # 下载限制

    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)  # 5分钟后session过期
    SESSION_REFRESH_EACH_REQUEST= True  # 每次请求刷新session
    ADMIN_PASSWORD = 'your_secure_admin_password'  # 改为你的实际管理员密码
    SESSION_COOKIE_SECURE = True  # 生产环境应启用
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'