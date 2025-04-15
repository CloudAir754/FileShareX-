from datetime import datetime,timedelta
import pytz
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
import re
import hashlib
from config import Config

# 设置时区为东八区
EASTERN_8 = pytz.timezone('Asia/Shanghai')


# 数据库初始化和配置
db = SQLAlchemy()  # 创建SQLAlchemy实例，用于数据库操作

def init_db(app):
    """初始化数据库配置"""
    basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前文件所在目录的绝对路径
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'filecodes.db')  # 使用SQLite数据库，文件名为filecodes.db
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 禁用SQLAlchemy的事件系统（节省资源）
    
    db.init_app(app)  # 绑定Flask应用
    with app.app_context():
        db.create_all()  # 创建所有定义的表


# 数据模型（文件记录表）
class FileRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    code = db.Column(db.String(32), unique=True, nullable=False)  # 唯一提取码（不允许空值）
    md5_filename = db.Column(db.String(32), nullable=False)  # 文件MD5哈希值作为存储名（防重复）
    original_filename = db.Column(db.String(256), nullable=False)  # 原始文件名
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    file_type = db.Column(db.String(32))  # 文件扩展名（如pdf、jpg）
    uploader_ip = db.Column(db.String(45))  # 上传者IP（支持IPv6，最长45字符）
    created_at = db.Column(db.DateTime, default=datetime.now(EASTERN_8))  # 创建时间（UTC）
    expires_at = db.Column(db.DateTime(timezone=True))  # 添加 timezone=True
    download_count = db.Column(db.Integer, default=0)  # 下载次数统计
    max_downloads = db.Column(db.Integer, default=1)  # 最大允许下载次数（0表示无限制）
    is_active = db.Column(db.Boolean, default=True)  # 是否启用（管理员可禁用）
    description = db.Column(db.String(500))  # 文件描述（可选）

    # 关联关系：一对多（一个文件对应多条下载记录）
    downloads = db.relationship('DownloadRecord', backref='file', lazy=True, cascade="all, delete-orphan")

    def is_valid(self):
        """检查文件是否有效（未过期、未超下载次数、已启用）"""
        if not self.is_active:
            return False
        if self.max_downloads > 0 and self.download_count >= self.max_downloads:
            return False
        if self.expires_at :
            now = datetime.now(EASTERN_8)
            expires_at = self.expires_at.replace(tzinfo=EASTERN_8) if self.expires_at.tzinfo is None else self.expires_at
            return now <= expires_at
        return True
    
# 下载记录表
class DownloadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    file_id = db.Column(db.Integer, db.ForeignKey('file_record.id'), nullable=False)  # 外键关联FileRecord
    downloader_ip = db.Column(db.String(45))  # 下载者IP
    download_time = db.Column(db.DateTime, default=datetime.now(EASTERN_8))  # 下载时间（UTC）
    user_agent = db.Column(db.String(256))  # 用户浏览器标识（用于日志分析）


# 工具函数
def generate_md5_filename(file_stream):
    """生成文件的MD5哈希值作为存储名（避免文件名冲突）"""
    md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b''):  # 分块读取文件（节省内存）
        md5.update(chunk)
    file_stream.seek(0)  # 重置文件指针位置
    return md5.hexdigest()  # 返回32位MD5字符串


def safe_filename(filename):
    """清理文件名中的非法字符（防止路径遍历攻击）"""
    basename, ext = os.path.splitext(filename)
    basename = re.sub(r'[\\/*?:"<>|]', "", basename)  # 移除非法字符
    basename = basename.strip()  # 去除首尾空格
    
    # 处理空文件名的情况（例如用户上传了一个无名称的文件）
    if not basename:
        basename = f"file_{int(datetime.now().timestamp())}"  # 用时间戳生成默认名
    
    # 确保扩展名格式正确（如".txt"而非"txt"）
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    
    return f"{basename}{ext}"


# 创建管理员登录尝试记录模型
class AdminLoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(45), nullable=False)
    attempt_time = db.Column(db.DateTime, default=datetime.now(EASTERN_8))
    username = db.Column(db.String(50))
    blocked_until = db.Column(db.DateTime)
    successful = db.Column(db.Boolean, default=False)

# 管理员登录防护函数
def check_admin_login_attempt(ip):
    now = datetime.now(EASTERN_8)
    block_time = timedelta(seconds=Config.ADMIN_LOGIN_BLOCK_TIME)
    
    # 检查是否已被封锁
    blocked = AdminLoginAttempt.query.filter(
        AdminLoginAttempt.ip == ip,
        AdminLoginAttempt.blocked_until > now
    ).first()
    
    if blocked:
        remaining_time = (blocked.blocked_until - now).seconds
        return False, f"管理员登录尝试过于频繁，请等待 {remaining_time} 秒后再试"
    
    # 检查最近失败尝试次数
    recent_failures = AdminLoginAttempt.query.filter(
        AdminLoginAttempt.ip == ip,
        AdminLoginAttempt.attempt_time > now - block_time,
        AdminLoginAttempt.successful == False
    ).count()
    
    if recent_failures >= Config.ADMIN_LOGIN_ATTEMPTS:
        # 封锁IP
        blocked_until = now + block_time
        new_block = AdminLoginAttempt(
            ip=ip,
            blocked_until=blocked_until,
            successful=False
        )
        db.session.add(new_block)
        db.session.commit()
        return False, f"管理员登录尝试次数过多，IP已被暂时封锁{block_time.total_seconds()/60}分钟"
    
    return True, ""