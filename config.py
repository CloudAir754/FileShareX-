import os

class Config:
    SECRET_KEY =  '1234'
    UPLOAD_FOLDER = 'files'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx', 'xls', 'xlsx'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    DEFAULT_EXPIRE_DAYS = 7  # 默认7天后过期
    CODE_LENGTH = 6  # 提取码长度
    CLEAR_ON_STARTUP = True