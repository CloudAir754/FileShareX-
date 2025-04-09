from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for, flash
from models import db, FileRecord, init_db, generate_md5_filename, safe_filename,DownloadRecord
from config import Config
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import random
import string
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
init_db(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_code(length=Config.CODE_LENGTH):
    """生成指定位数的字母数字混合提取码（大小写敏感）"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        
        if not code:
            flash('请输入提取码', 'error')
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
            
        # file_record.download_count += 1
        db.session.commit()
        
        return redirect(url_for('download_file', code=code))
    
    return render_template('index.html')

@app.route('/admin/add', methods=['GET', 'POST'])
def add_file():
    if request.method == 'POST':
        if request.form.get('admin_key') != app.config['SECRET_KEY']:
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


@app.route('/download/<code>')
def download_file(code):
    file_record = FileRecord.query.filter_by(code=code).first()
    
    if not file_record or not file_record.is_valid():
        abort(404)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_record.md5_filename)
    
    if not os.path.exists(filepath):
        abort(404)
    
    # 创建下载记录
    download_record = DownloadRecord(
        file_id=file_record.id,
        downloader_ip=request.remote_addr,
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


# 添加到 app.py 中的路由部分
@app.route('/admin')
def admin_home():
    if request.args.get('admin_key') != app.config['SECRET_KEY']:
        abort(403)
    
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
def admin_search():
    if request.args.get('admin_key') != app.config['SECRET_KEY']:
        abort(403)
    
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
def delete_file(file_id):
    if request.args.get('admin_key') != app.config['SECRET_KEY']:
        abort(403)
    
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
    
    return redirect(url_for('admin_search', admin_key=request.args.get('admin_key')))

@app.route('/admin/file/<int:file_id>/toggle', methods=['POST'])
def toggle_file(file_id):
    if request.args.get('admin_key') != app.config['SECRET_KEY']:
        abort(403)
    
    file_record = FileRecord.query.get_or_404(file_id)
    file_record.is_active = not file_record.is_active
    db.session.commit()
    
    action = "激活" if file_record.is_active else "禁用"
    flash(f'文件已{action}', 'success')
    return redirect(url_for('admin_search', admin_key=request.args.get('admin_key')))




@app.route('/admin/records')
def view_records():
    if request.args.get('admin_key') != app.config['SECRET_KEY']:
        abort(403)
    
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

    app.run(debug=True)