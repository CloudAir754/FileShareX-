import os
from datetime import timedelta
import pytz

class Config:
    SECRET_KEY = '12345'  # Flask应用的安全密钥，用于加密会话数据
    UPLOAD_FOLDER = 'files'  # 文件上传保存的目录
    ALLOWED_EXTENSIONS = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
    'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'],
    'archives': ['zip', 'rar', '7z', 'tar', 'gz'], 
    'audio': ['mp3', 'wav', 'ogg', 'flac'],
    'video': ['mp4', 'avi', 'mov', 'mkv', 'flv'],
    # 添加其他需要的类型
    }
    # 合并所有允许的扩展名
    ALLOWED_EXTENSIONS_FLAT = [ext for group in ALLOWED_EXTENSIONS.values() for ext in group]

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB，限制上传文件的最大大小
    DEFAULT_EXPIRE_DAYS = 7  # 默认7天后过期，文件记录的默认有效期
    CODE_LENGTH = 6  # 提取码的长度（字符数）
    CLEAR_ON_STARTUP = True  # 启动时是否清空数据库和上传文件夹（用于开发和测试）
    
    # 速率限制配置
    RATE_LIMIT_DEFAULT = "200 per day, 50 per hour"  # 全局默认请求限制（每天200次，每小时50次）
    RATE_LIMIT_INDEX = "10 per minute"  # 首页/提取码尝试的请求限制（每分钟10次）
    RATE_LIMIT_DOWNLOAD = "3 per minute"  # 下载请求的限制（每分钟3次）
    RATE_LIMIT_ADMIN = "5 per minute"  # 新增的管理员接口速率限制

    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)  # 会话有效期5分钟
    SESSION_REFRESH_EACH_REQUEST = True  # 每次请求都刷新会话有效期
    ADMIN_PASSWORD = '111'  # 管理员登录密码（应改为强密码）
    
    # 安全相关的cookie设置
    SESSION_COOKIE_SECURE = False  # 只允许HTTPS传输cookie（生产环境应启用）
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF攻击的cookie策略

    # 新增的密码(提取码)爆破防护配置
    PASSWORD_MAX_ATTEMPTS = 2  # 5分钟内最多尝试次数
    PASSWORD_BLOCK_TIME = 300  # 封锁时间(秒)
    DOWNLOAD_FREQUENCY_LIMIT = 3  # 下载频率检查窗口（5分钟）内同一文件下载次数限制
    DOWNLOAD_FREQUENCY_WINDOW = 5  # 下载频率检查窗口(分钟)

    ADMIN_LOGIN_ATTEMPTS = 5  # 允许的最大尝试次数
    ADMIN_LOGIN_BLOCK_TIME = 300  # 封锁时间(秒)
    ADMIN_LOGIN_DELAY = 2  # 失败后的延迟响应(秒)
    ADMIN_SESSION_TIMEOUT = 1800  # 会话超时时间(秒)

    TIMEZONE = pytz.timezone('Asia/Shanghai')
    DEFALUT_ITEM_EVERY_PAGE = 5 # 默认分页项数，比较小主要是为了方便测试