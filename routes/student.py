from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from models import Post
from forms import StudentPostForm
from extensions import db
import os
from werkzeug.utils import secure_filename
import uuid

student_bp = Blueprint('student', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@student_bp.route('/post', methods=['GET', 'POST'])
def post_question():
    form = StudentPostForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                file.save(filepath)
                image_filename = unique_name
            else:
                flash('Image file type not allowed.', 'danger')
                return render_template('student_post.html', form=form)

        post = Post(
            jut_number=form.jut_number.data,
            subject=form.subject.data,
            text_content=form.text_content.data,
            image_filename=image_filename
        )
        db.session.add(post)
        db.session.commit()
        flash('Your question has been submitted successfully!', 'success')
        return redirect(url_for('student.thank_you'))

    return render_template('student_post.html', form=form)

@student_bp.route('/thank-you')
def thank_you():
    return render_template('student_thanks.html')