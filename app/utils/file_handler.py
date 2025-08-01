import os
from werkzeug.utils import secure_filename
from flask import current_app, flash
from datetime import datetime

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, course_id):
    if not file or file.filename == '':
        flash('No selected file', 'error')
        return None
    
    if not allowed_file(file.filename):
        flash('File type not allowed', 'error')
        return None
    
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], course_id)
    
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    return {
        'filename': filename,
        'path': file_path,
        'upload_date': datetime.now().isoformat(),
        'size': file_size
    }