from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
from werkzeug.utils import secure_filename
import re

db = SQLAlchemy()

class FileRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)  # 提取码
    md5_filename = db.Column(db.String(32), nullable=False)      # 存储用的MD5文件名
    original_filename = db.Column(db.String(256), nullable=False) # 原始文件名
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    max_downloads = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)

    def is_valid(self):
        """检查提取码是否有效"""
        if not self.is_active:
            return False
        
        if self.max_downloads > 0 and self.download_count >= self.max_downloads:
            return False
            
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
            
        return True

def init_db(app):
    """初始化数据库"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'filecodes.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    with app.app_context():
        db.create_all()

def generate_md5_filename(file_stream):
    """生成文件的MD5哈希作为文件名"""
    md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b''):
        md5.update(chunk)
    file_stream.seek(0)  # 重置文件指针
    return md5.hexdigest()

def safe_filename(filename):
    """安全处理文件名，保留UTF-8字符和正确扩展名"""
    # 确保文件名有扩展名
    basename, ext = os.path.splitext(filename)
    
    # 清理非法字符但保留UTF-8
    basename = re.sub(r'[\\/*?:"<>|]', "", basename)  # 移除非法字符
    basename = basename.strip()  # 去除前后空格
    
    # 如果名称被完全清理掉，使用时间戳
    if not basename:
        basename = f"file_{int(datetime.now().timestamp())}"
    
    # 确保扩展名以点开头
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    
    # 组合完整文件名
    return f"{basename}{ext}"