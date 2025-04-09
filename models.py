from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
from werkzeug.utils import secure_filename
import re

db = SQLAlchemy()

class FileRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    md5_filename = db.Column(db.String(32), nullable=False)
    original_filename = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    download_count = db.Column(db.Integer, default=0)
    max_downloads = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)

    def is_valid(self):
        if not self.is_active:
            return False
        
        if self.max_downloads > 0 and self.download_count >= self.max_downloads:
            return False
            
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
            
        return True

def init_db(app):
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'filecodes.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    with app.app_context():
        db.create_all()

def generate_md5_filename(file_stream):
    md5 = hashlib.md5()
    for chunk in iter(lambda: file_stream.read(4096), b''):
        md5.update(chunk)
    file_stream.seek(0)
    return md5.hexdigest()

def safe_filename(filename):
    basename, ext = os.path.splitext(filename)
    basename = re.sub(r'[\\/*?:"<>|]', "", basename)
    basename = basename.strip()
    
    if not basename:
        basename = f"file_{int(datetime.now().timestamp())}"
    
    if ext and not ext.startswith('.'):
        ext = '.' + ext
    
    return f"{basename}{ext}"