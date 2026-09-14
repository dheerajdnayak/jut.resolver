from flask import Flask, render_template, request, jsonify, current_app
from config import Config
from extensions import db, login_manager, bcrypt
from routes.student import student_bp
from routes.lecturer import lecturer_bp
from routes.admin import admin_bp
from models import Post, PublicComment, User, Vote, ChatMessage
from forms import PublicCommentForm, StudentPostForm
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
import uuid


# ---------- serializers ----------
def serialize_post(post, include_comments=False):
    data = {
        'id': post.id,
        'jut_number': post.jut_number,
        'subject': post.subject,
        'subject_label': post.subject.capitalize(),
        'text_content': post.text_content or '',
        'image_filename': post.image_filename,
        'image_url': f'/static/uploads/{post.image_filename}' if post.image_filename else None,
        'created_at': post.created_at.strftime('%Y-%m-%d %H:%M'),
        'created_at_short': post.created_at.strftime('%b %d, %H:%M'),
        'status': post.status,
    }
    if include_comments:
        data['comments'] = [serialize_comment(c) for c in post.public_comments.order_by(PublicComment.created_at.asc()).all()]
    return data


def serialize_comment(c):
    return {
        'id': c.id, 'post_id': c.post_id,
        'name': c.name or 'Anonymous',
        'text': c.text,
        'created_at': c.created_at.strftime('%Y-%m-%d %H:%M'),
        'created_at_short': c.created_at.strftime('%H:%M'),
    }


def serialize_message(m):
    return {
        'id': m.id, 'post_id': m.post_id,
        'lecturer_name': m.lecturer.name,
        'message': m.message,
        'created_at': m.created_at.strftime('%Y-%m-%d %H:%M'),
        'created_at_short': m.created_at.strftime('%H:%M'),
    }


def get_vote_stats(post):
    rows = db.session.query(Vote.option, func.count(Vote.id)).filter(Vote.post_id == post.id).group_by(Vote.option).all()
    counts = {opt: 0 for opt in ['GRACE', '1', '2', '3', '4', 'NUMERICAL']}
    for opt, cnt in rows:
        counts[opt] = cnt
    num_vals = [r[0] for r in db.session.query(Vote.numerical_value)
                .filter(Vote.post_id == post.id, Vote.option == 'NUMERICAL').all() if r[0] is not None]
    total = User.query.filter_by(subject=post.subject, is_admin=False).count()
    voted = Vote.query.filter_by(post_id=post.id).count()
    fraction = f"{voted}/{total}" if total else "0/0"
    return counts, fraction, num_vals


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'lecturer.login'
    login_manager.login_message_category = 'info'
    bcrypt.init_app(app)

    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(admin_bp)

    # ---------------- MAIN FEED ----------------
    @app.route('/')
    def index():
        posts = Post.query.filter_by(status='active').order_by(Post.created_at.desc()).all()
        form = PublicCommentForm()
        return render_template('index.html', posts=posts, form=form)

    # ---------------- API: SUBMIT POST ----------------
    @app.route('/api/submit', methods=['POST'])
    def api_submit():
        form = StudentPostForm()
        if not form.validate_on_submit():
            return jsonify({'ok': False, 'errors': form.errors}), 400

        image_filename = None
        if form.image.data:
            file = form.image.data
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if ext in current_app.config['ALLOWED_EXTENSIONS']:
                unique_name = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name))
                image_filename = unique_name

        post = Post(
            jut_number=form.jut_number.data,
            subject=form.subject.data,
            text_content=form.text_content.data,
            image_filename=image_filename
        )
        db.session.add(post)
        db.session.commit()

        payload = serialize_post(post, include_comments=True)
        socketio.emit('new_post', payload, room='feed')
        socketio.emit('new_post', payload, room='admin')
        socketio.emit('new_post', payload, room=f'subject_{post.subject}')
        return jsonify({'ok': True, 'post': payload})

    # ---------------- API: DATA ----------------
    @app.route('/api/posts')
    def api_posts():
        posts = Post.query.filter_by(status='active').order_by(Post.created_at.desc()).all()
        return jsonify([serialize_post(p, include_comments=True) for p in posts])

    @app.route('/api/lecturer/posts')
    def api_lecturer_posts():
        if not current_user.is_authenticated or current_user.is_admin:
            return jsonify({'ok': False}), 401
        posts = Post.query.filter_by(subject=current_user.subject, status='active').order_by(Post.created_at.desc()).all()
        return jsonify([serialize_post(p) for p in posts])

    @app.route('/api/admin/dashboard')
    def api_admin_dashboard():
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'ok': False}), 401
        def build(posts):
            out = []
            for p in posts:
                counts, fraction, nums = get_vote_stats(p)
                out.append({'post': serialize_post(p), 'counts': counts,
                            'fraction': fraction, 'numerical_values': nums})
            return out
        active = Post.query.filter_by(status='active').order_by(Post.created_at.desc()).all()
        updated = Post.query.filter_by(status='updated').order_by(Post.created_at.desc()).all()
        return jsonify({'active': build(active), 'updated': build(updated)})

    # ---------------- SOCKET EVENTS ----------------
    @socketio.on('join_rooms')
    def on_join(data):
        for r in (data.get('rooms') or []):
            join_room(r)

    @socketio.on('leave_room')
    def on_leave(data):
        r = data.get('room')
        if r:
            leave_room(r)

    @socketio.on('post_comment')
    def on_comment(data):
        post_id = data.get('post_id')
        name = (data.get('name') or '').strip() or 'Anonymous'
        text = (data.get('text') or '').strip()
        if not post_id or not text:
            return
        post = Post.query.get(post_id)
        if not post:
            return
        comment = PublicComment(post_id=post.id, name=name, text=text)
        db.session.add(comment)
        db.session.commit()
        payload = serialize_comment(comment)
        emit('new_public_comment', payload, room='feed')
        emit('new_public_comment', payload, room=f'post_{post.id}')

    @socketio.on('send_lecturer_message')
    def on_msg(data):
        if not current_user.is_authenticated or current_user.is_admin:
            return
        post_id = data.get('post_id')
        text = (data.get('message') or '').strip()
        if not post_id or not text:
            return
        post = Post.query.get(post_id)
        if not post or post.subject != current_user.subject:
            return
        msg = ChatMessage(post_id=post.id, lecturer_id=current_user.id, message=text)
        db.session.add(msg)
        db.session.commit()
        payload = serialize_message(msg)
        emit('new_lecturer_message', payload, room=f'post_{post.id}')

    @socketio.on('cast_vote')
    def on_vote(data):
        if not current_user.is_authenticated or current_user.is_admin:
            return
        post_id = data.get('post_id')
        option = data.get('option')
        if not post_id or option not in ('GRACE', '1', '2', '3', '4', 'NUMERICAL'):
            return
        post = Post.query.get(post_id)
        if not post or post.subject != current_user.subject:
            return
        num_val = None
        if option == 'NUMERICAL':
            try:
                num_val = float(data.get('numerical_value'))
            except (TypeError, ValueError):
                return
        existing = Vote.query.filter_by(post_id=post.id, lecturer_id=current_user.id).first()
        if existing:
            existing.option = option
            existing.numerical_value = num_val
        else:
            db.session.add(Vote(post_id=post.id, lecturer_id=current_user.id,
                                option=option, numerical_value=num_val))
        db.session.commit()
        counts, fraction, nums = get_vote_stats(post)
        payload = {'post_id': post.id, 'counts': counts, 'fraction': fraction, 'numerical_values': nums}
        emit('vote_changed', payload, room='admin')
        emit('vote_changed', payload, room=f'post_{post.id}')
        # confirm to sender
        emit('your_vote_saved', {'post_id': post.id, 'option': option, 'numerical_value': num_val})

    @socketio.on('mark_post_updated')
    def on_mark(data):
        if not current_user.is_authenticated or not current_user.is_admin:
            return
        post = Post.query.get(data.get('post_id'))
        if not post:
            return
        post.status = 'updated'
        db.session.commit()
        payload = {'post_id': post.id, 'status': 'updated'}
        for room in ['admin', 'feed', f'subject_{post.subject}']:
            emit('post_status_changed', payload, room=room)

    @socketio.on('delete_post')
    def on_delete(data):
        if not current_user.is_authenticated or not current_user.is_admin:
            return
        post = Post.query.get(data.get('post_id'))
        if not post:
            return
        subject = post.subject
        post_id = post.id
        db.session.delete(post)
        db.session.commit()
        payload = {'post_id': post_id}
        for room in ['admin', 'feed', f'subject_{subject}']:
            emit('post_deleted', payload, room=room)

    # ADMINCONTACTROUTE
    @app.route('/contact')
    def contact():
        return "ADMIN CONTACT details here; admin will give lecturers link to `/lecturer/signup`"

    # ---------------- DB SETUP ----------------
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(is_admin=True).first():
            admin = User(name='admin', subject=None, is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin: admin / admin123")

    return app, socketio


if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)