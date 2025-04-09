import os

class Config:
    SECRET_KEY =  '1234'
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