from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from extensions import db, login_manager, bcrypt
from routes.student import student_bp
from routes.lecturer import lecturer_bp
from routes.admin import admin_bp
from models import Post, PublicComment, User   # ✅ import User here
from forms import PublicCommentForm
from flask_socketio import SocketIO, emit, join_room
from flask_login import current_user
import os



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

    # Register blueprints
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(lecturer_bp)
    app.register_blueprint(admin_bp)

    @app.route('/contact')
    def admincontact():
        return "ADMIN CONTACT NUMBER; admin will give link for /lecturer/signup"

    # ----- Main route (public) -----
    @app.route('/', methods=['GET', 'POST'])
    def index():
        form = PublicCommentForm()
        if form.validate_on_submit():
            post_id = request.form.get('post_id')
            if not post_id:
                flash('Invalid post.', 'danger')
                return redirect(url_for('index'))
            post = Post.query.get(int(post_id))
            if not post:
                flash('Post not found.', 'danger')
                return redirect(url_for('index'))
            comment = PublicComment(
                post_id=post.id,
                name=form.name.data or 'Anonymous',
                text=form.text.data
            )
            db.session.add(comment)
            db.session.commit()
            socketio.emit('new_public_comment', {
                'post_id': post.id,
                'name': comment.name,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'comment_id': comment.id
            }, room=f'post_{post.id}')
            flash('Comment posted!', 'success')
            return redirect(url_for('index'))

        posts = Post.query.filter_by(status='active').order_by(Post.created_at.desc()).all()
        return render_template('index.html', posts=posts, form=form)

    # ----- SocketIO events -----
    @socketio.on('connect')
    def handle_connect():
        print('Client connected')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('join_post')
    def on_join(data):
        post_id = data.get('post_id')
        if post_id:
            join_room(f'post_{post_id}')
            print(f'Client joined room post_{post_id}')

    @socketio.on('new_lecturer_message')
    def handle_lecturer_message(data):
        if not current_user.is_authenticated:
            return
        post_id = data.get('post_id')
        msg_text = data.get('message')
        if not post_id or not msg_text:
            return
        from models import ChatMessage
        msg = ChatMessage(
            post_id=post_id,
            lecturer_id=current_user.id,
            message=msg_text
        )
        db.session.add(msg)
        db.session.commit()
        emit('new_lecturer_message', {
            'post_id': post_id,
            'lecturer_name': current_user.name,
            'message': msg_text,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M')
        }, room=f'post_{post_id}', include_self=False)

    # Create tables and default admin
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User(name='admin', subject=None, is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin/admin123")

    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)