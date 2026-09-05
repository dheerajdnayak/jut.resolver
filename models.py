from extensions import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(20))  # 'phy', 'chem', 'maths'
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jut_number = db.Column(db.String(50), nullable=False)          # NEW
    subject = db.Column(db.String(20), nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # 'active', 'updated', 'deleted'

    votes = db.relationship('Vote', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Post {self.id} JUT#{self.jut_number}>'

class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    option = db.Column(db.String(20), nullable=False)  # 'GRACE', '1', '2', '3', '4', 'NUMERICAL'
    numerical_value = db.Column(db.Float, nullable=True)  # only for NUMERICAL option
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('post_id', 'lecturer_id', name='unique_vote'),)

    def __repr__(self):
        return f'<Vote post={self.post_id} lecturer={self.lecturer_id} option={self.option}>'

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    lecturer = db.relationship('User', backref='messages')

    def __repr__(self):
        return f'<ChatMessage post={self.post_id} lecturer={self.lecturer_id}>'