import os
from datetime import timedelta

class Config:
    SECRET_KEY = '12345'  # Flask应用的安全密钥，用于加密会话数据
    UPLOAD_FOLDER = 'files'  # 文件上传保存的目录
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'
                          , 'zip', 'doc', 'docx', 'xls', 'xlsx'}  # 允许上传的文件扩展名
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB，限制上传文件的最大大小
    DEFAULT_EXPIRE_DAYS = 7  # 默认7天后过期，文件记录的默认有效期
    CODE_LENGTH = 6  # 提取码的长度（字符数）
    CLEAR_ON_STARTUP = True  # 启动时是否清空数据库和上传文件夹（用于开发和测试）
    
    # 速率限制配置
    RATE_LIMIT_DEFAULT = "200 per day, 50 per hour"  # 全局默认请求限制（每天200次，每小时50次）
    RATE_LIMIT_INDEX = "10 per minute"  # 首页/提取码尝试的请求限制（每分钟10次）
    RATE_LIMIT_DOWNLOAD = "3 per minute"  # 下载请求的限制（每分钟3次）

    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)  # 会话有效期5分钟
    SESSION_REFRESH_EACH_REQUEST = True  # 每次请求都刷新会话有效期
    ADMIN_PASSWORD = '111'  # 管理员登录密码（应改为强密码）
    
    # 安全相关的cookie设置
    SESSION_COOKIE_SECURE = False  # 只允许HTTPS传输cookie（生产环境应启用）
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF攻击的cookie策略