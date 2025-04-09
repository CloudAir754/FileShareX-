from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for, flash, session
from models import db, FileRecord, init_db, generate_md5_filename, safe_filename,DownloadRecord
from config import Config
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import random
import string
from werkzeug.exceptions import HTTPException
from functools import wraps

from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for, flash, session
from models import db, FileRecord, init_db, generate_md5_filename, safe_filename, DownloadRecord
from config import Config
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import random
import string
from werkzeug.exceptions import HTTPException
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']  # 设置session密钥

# 初始化数据库
init_db(app)

# 初始化速率限制器
limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # 使用客户端IP作为限制依据
    default_limits=["200 per day", "50 per hour"]  # 全局默认限制
)

# 密码尝试记录
password_attempts = {}

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.errorhandler(RequestEntityTooLarge)
def handle_413(error):
    # 从配置中获取最大文件大小（转换为MB）
    max_size = app.config.get('MAX_CONTENT_LENGTH', 0)
    if max_size:
        max_size = f"{round(max_size / (1024 * 1024))}MB"
    else:
        max_size = "未设置"
        
        # 获取来源页面（如果存在）
    referrer = request.headers.get('Referer')
    
    return render_template(
        '413.html',
        max_size=max_size,
        referrer=referrer
    ), 413


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args,**kwargs)
    return decorated_function

def check_brute_force(ip, code):
    """检查密码爆破尝试"""
    now = time.time()
    
    # 初始化IP记录
    if ip not in password_attempts:
        password_attempts[ip] = {'attempts': [], 'blocked_until': 0}
    
    # 检查是否被封锁
    if password_attempts[ip]['blocked_until'] > now:
        remaining_time = int(password_attempts[ip]['blocked_until'] - now)
        return False, f"尝试过于频繁，请等待 {remaining_time} 秒后再试"
    
    # 记录本次尝试
    password_attempts[ip]['attempts'].append(now)
    
    # 清理过期的尝试记录（只保留最近5分钟内的）
    password_attempts[ip]['attempts'] = [
        t for t in password_attempts[ip]['attempts'] 
        if t > now - 300
    ]
    
    # 检查尝试次数
    max_attempts = 10  # 5分钟内最多尝试10次
    if len(password_attempts[ip]['attempts']) > max_attempts:
        # 封锁IP 5分钟
        password_attempts[ip]['blocked_until'] = now + 300
        return False, "尝试次数过多，IP已被暂时封锁5分钟"
    
    return True, ""

def check_download_frequency(ip, file_id):
    """检查下载频率"""
    now = datetime.utcnow()
    
    # 检查同一IP在短时间内对同一文件的下载次数
    recent_downloads = DownloadRecord.query.filter(
        DownloadRecord.downloader_ip == ip,
        DownloadRecord.file_id == file_id,
        DownloadRecord.download_time > now - timedelta(minutes=5)
    ).count()
    
    if recent_downloads >= 3:  # 5分钟内最多下载3次
        return False
    
    return True

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # 限制每分钟10次请求
def index():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        ip = get_remote_address()
        
        if not code:
            flash('请输入提取码', 'error')
            return redirect(url_for('index'))
        
        # 检查爆破尝试
        is_allowed, message = check_brute_force(ip, code)
        if not is_allowed:
            flash(message, 'error')
            return redirect(url_for('index'))
        
        file_record = FileRecord.query.filter_by(code=code).first()
        
        if not file_record:
            flash('无效的提取码', 'error')
            return redirect(url_for('index'))
            
        if not file_record.is_valid():
            if file_record.expires_at and datetime.utcnow() > file_record.expires_at:
                flash('提取码已过期', 'error')
            elif file_record.max_downloads > 0 and file_record.download_count >= file_record.max_downloads:
                flash('提取码已达到最大下载次数', 'error')
            else:
                flash('提取码已失效', 'error')
            return redirect(url_for('index'))
            
        return redirect(url_for('download_file', code=code))
    
    return render_template('index.html')

@app.route('/download/<code>')
@limiter.limit("3 per minute")  # 限制每分钟3次下载
def download_file(code):
    ip = get_remote_address()
    file_record = FileRecord.query.filter_by(code=code).first()
    
    if not file_record or not file_record.is_valid():
        abort(404)
    
    # 检查下载频率
    if not check_download_frequency(ip, file_record.id):
        flash('下载过于频繁，请稍后再试', 'error')
        return redirect(url_for('index'))
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_record.md5_filename)
    
    if not os.path.exists(filepath):
        abort(404)
    
    # 创建下载记录
    download_record = DownloadRecord(
        file_id=file_record.id,
        downloader_ip=ip,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(download_record)
    
    # 更新下载计数
    file_record.download_count += 1
    db.session.commit()
    
    response = send_from_directory(
        app.config['UPLOAD_FOLDER'],
        file_record.md5_filename,
        as_attachment=True,
        download_name=file_record.original_filename
    )
    
    return response


def generate_code(length=Config.CODE_LENGTH):
    """生成指定位数的字母数字混合提取码（大小写敏感）"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args,**kwargs)
    return decorated_function


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('admin_password', '')
        
        # 验证密码
        if password == app.config['SECRET_KEY']:
            # 设置session标记用户已登录
            session['admin_logged_in'] = True
            session.permanent = True  # 设置session为持久化
            flash('登录成功', 'success')
            return redirect(url_for('admin_home'))
        else:
            # 密码错误，返回登录页并显示错误信息
            return render_template('admin_login.html', error="密码错误，请重试")
    
    # GET请求，显示登录页面
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    # 清除session中的登录标记
    session.pop('admin_logged_in', None)
    flash('您已成功登出', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def add_file():
    if request.method == 'POST':
        if not session.get('admin_logged_in'):
            abort(403)
            
        if 'file' not in request.files:
            flash('没有上传文件', 'error')
            return redirect(url_for('add_file'))
            
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(url_for('add_file'))
        
        try:
            max_attempts = 10
            for _ in range(max_attempts):
                code = generate_code()
                if not FileRecord.query.filter_by(code=code).first():
                    break
            else:
                flash('无法生成唯一提取码，请重试', 'error')
                return redirect(url_for('add_file'))
            
            original_filename = request.files['file'].filename
            safe_name = safe_filename(original_filename)
            md5_filename = generate_md5_filename(file.stream)
            
            # 获取文件信息
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            file_type = os.path.splitext(original_filename)[1].lower().lstrip('.')
            
            expire_days = int(request.form.get('expire_days', app.config['DEFAULT_EXPIRE_DAYS']))
            expires_at = datetime.utcnow() + timedelta(days=expire_days)
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], md5_filename)
            file.save(filepath)
            
            new_record = FileRecord(
                code=code,
                md5_filename=md5_filename,
                original_filename=original_filename,
                file_size=file_size,
                file_type=file_type,
                uploader_ip=request.remote_addr,  # 记录上传者IP
                expires_at=expires_at,
                max_downloads=int(request.form.get('max_downloads', 1)),
                description=request.form.get('description', '')  # 文件描述
            )
            
            db.session.add(new_record)
            db.session.commit()
            
            flash(f'文件添加成功！提取码: {code}', 'success')
            return redirect(url_for('add_file'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'文件上传失败: {str(e)}', 'error')
            app.logger.error(f"文件上传错误: {str(e)}", exc_info=True)
            return redirect(url_for('add_file'))
    
    return render_template('admin_add.html')

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
def handle_40x_error(error):
    code = getattr(error, 'code', 500)
    return render_template('40x.html'), code

@app.errorhandler(500)
def handle_50x_error(error):
    return render_template('50x.html'), 500

@app.errorhandler(Exception)
def handle_exception(error):
    # 传递HTTP异常
    if isinstance(error, HTTPException):
        return error
    
    # 非HTTP异常，记录错误并返回500页面
    app.logger.error(f"服务器错误: {str(error)}", exc_info=True)
    return render_template('50x.html'), 500

@app.cli.command('cleanup')
def cleanup():
    # 清理过期文件记录
    expired_records = FileRecord.query.filter(
        FileRecord.expires_at < datetime.utcnow()
    ).all()
    
    for record in expired_records:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], record.md5_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(record)
    
    # 清理30天前的下载记录
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    old_downloads = DownloadRecord.query.filter(
        DownloadRecord.download_time < thirty_days_ago
    ).delete()
    
    db.session.commit()
    print(f"清理了 {len(expired_records)} 个过期文件记录和 {old_downloads} 条旧下载记录")

@app.route('/admin')
@admin_required
def admin_home():
    # 统计信息
    total_files = FileRecord.query.count()
    active_files = FileRecord.query.filter(FileRecord.is_active == True).count()
    total_downloads = db.session.query(db.func.sum(FileRecord.download_count)).scalar() or 0
    
    # 最近上传的文件
    recent_files = FileRecord.query.order_by(FileRecord.created_at.desc()).limit(5).all()
    
    return render_template('admin_home.html', 
                         total_files=total_files,
                         active_files=active_files,
                         total_downloads=total_downloads,
                         recent_files=recent_files)

@app.route('/admin/search')
@admin_required
def admin_search():
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if query:
        # 搜索文件名、提取码或描述
        search = f"%{query}%"
        files = FileRecord.query.filter(
            (FileRecord.original_filename.like(search)) |
            (FileRecord.code.like(search)) |
            (FileRecord.description.like(search))
        ).order_by(FileRecord.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        files = FileRecord.query.order_by(FileRecord.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin_records.html', files=files, query=query)

@app.route('/admin/file/<int:file_id>/delete', methods=['POST'])
@admin_required
def delete_file(file_id):
    file_record = FileRecord.query.get_or_404(file_id)
    
    try:
        # 删除物理文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_record.md5_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 删除数据库记录
        db.session.delete(file_record)
        db.session.commit()
        
        flash('文件删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除失败: {str(e)}', 'error')
        app.logger.error(f"删除文件失败: {str(e)}", exc_info=True)
    
    return redirect(url_for('admin_search'))

@app.route('/admin/file/<int:file_id>/toggle', methods=['POST'])
@admin_required
def toggle_file(file_id):
    file_record = FileRecord.query.get_or_404(file_id)
    file_record.is_active = not file_record.is_active
    db.session.commit()
    
    action = "激活" if file_record.is_active else "禁用"
    flash(f'文件已{action}', 'success')
    return redirect(url_for('admin_search'))

@app.route('/admin/records')
@admin_required
def view_records():
    # 获取文件记录和关联的下载记录
    files = FileRecord.query.order_by(FileRecord.created_at.desc()).all()
    
    return render_template('admin_records.html', files=files)

if __name__ == '__main__':
    if app.config['CLEAR_ON_STARTUP']:
        import shutil
        from sqlalchemy import inspect

        with app.app_context():
            inspector = inspect(db.engine)
            db.session.close()
            db.reflect()
            db.drop_all()
            print("已删除所有数据库表")
            
            upload_folder = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)
                print(f"已删除上传文件夹内容: {upload_folder}")
            
            db.create_all()
            print("已重新创建数据库表结构")
            
            os.makedirs(upload_folder, exist_ok=True)
            print(f"已重新创建上传文件夹: {upload_folder}")

    app.run('0.0.0.0', 5000, debug=False)