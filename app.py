from flask import Flask, render_template, request, send_from_directory, abort, redirect, url_for, flash
from models import db, FileRecord, init_db, generate_md5_filename,safe_filename
from config import Config
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import random
import string

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
init_db(app)

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def generate_code(length=Config.CODE_LENGTH):
    """生成指定位数的字母数字混合提取码（大小写敏感）"""
    chars = string.ascii_letters + string.digits  # 包含大小写字母和数字
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
            
        # 增加下载计数
        file_record.download_count += 1
        db.session.commit()
        
        return redirect(url_for('download_file', code=code))
    
    return render_template('index.html')

import os
import re
from datetime import datetime

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

@app.route('/admin/add', methods=['GET', 'POST'])
def add_file():
    if request.method == 'POST':
        # 简单身份验证示例
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
            # 生成唯一6位字母数字提取码
            max_attempts = 10
            for _ in range(max_attempts):
                code = generate_code()
                if not FileRecord.query.filter_by(code=code).first():
                    break
            else:
                flash('无法生成唯一提取码，请重试', 'error')
                return redirect(url_for('add_file'))
            
            # 获取文件信息
            # original_filename = secure_filename(file.filename)
            # md5_filename = generate_md5_filename(file.stream)

            # 修改这部分 - 使用新的safe_filename函数
            # 获取原始文件名（保留UTF-8编码）
            original_filename = request.files['file'].filename
            # 使用安全函数处理
            safe_name = safe_filename(original_filename)
            # 存储到数据库时保留原始文件名
            md5_filename = generate_md5_filename(file.stream)
            
            # 获取过期时间
            expire_days = int(request.form.get('expire_days', app.config['DEFAULT_EXPIRE_DAYS']))
            expires_at = datetime.utcnow() + timedelta(days=expire_days)
            
            # 保存文件
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], md5_filename)
            file.save(filepath)
            
            # 创建文件记录
            new_record = FileRecord(
                code=code,
                md5_filename=md5_filename,
                original_filename=original_filename,
                expires_at=expires_at,
                max_downloads=int(request.form.get('max_downloads', 1))
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
    """处理文件下载"""
    file_record = FileRecord.query.filter_by(code=code).first()
    
    if not file_record or not file_record.is_valid():
        abort(404)
    
    # 构建文件路径
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_record.md5_filename)
    
    # 检查文件是否存在
    if not os.path.exists(filepath):
        abort(404)
    
    # 发送文件，使用原始文件名作为下载时的文件名
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        file_record.md5_filename,
        as_attachment=True,
        download_name=file_record.original_filename
    )

@app.cli.command('cleanup')
def cleanup():
    """清理过期文件和数据库记录"""
    expired_records = FileRecord.query.filter(
        FileRecord.expires_at < datetime.utcnow()
    ).all()
    
    for record in expired_records:
        # 删除文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], record.md5_filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # 删除数据库记录
        db.session.delete(record)
    
    db.session.commit()
    print(f"清理了 {len(expired_records)} 个过期记录")



if __name__ == '__main__':
    if app.config['CLEAR_ON_STARTUP']:
        import shutil
        from sqlalchemy import inspect

        with app.app_context():
            # 获取数据库引擎和元数据
            inspector = inspect(db.engine)
            
            # 1. 删除所有表
            db.session.close()  # 确保没有活跃会话
            db.reflect()  # 加载当前数据库结构
            db.drop_all()  # 删除所有表
            print("已删除所有数据库表")
            
            # 2. 清理上传文件夹
            upload_folder = app.config['UPLOAD_FOLDER']
            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)
                print(f"已删除上传文件夹内容: {upload_folder}")
            
            # 3. 重新创建表结构
            db.create_all()
            print("已重新创建数据库表结构")
            
            # 4. 重新创建上传文件夹
            os.makedirs(upload_folder, exist_ok=True)
            print(f"已重新创建上传文件夹: {upload_folder}")

    app.run(debug=True)