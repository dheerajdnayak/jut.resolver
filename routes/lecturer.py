from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Post, Vote, ChatMessage
from forms import LecturerLoginForm, LecturerSignupForm, VoteForm, ChatMessageForm
from extensions import db
from sqlalchemy import func

lecturer_bp = Blueprint('lecturer', __name__, url_prefix='/lecturer')

@lecturer_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('lecturer.dashboard'))
    form = LecturerSignupForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(name=form.name.data).first()
        if existing:
            flash('User with that name already exists. Please login.', 'danger')
            return render_template('lecturer_signup.html', form=form)

        user = User(
            name=form.name.data,
            subject=form.subject.data,
            is_admin=False
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('lecturer.login'))
    return render_template('lecturer_signup.html', form=form)

@lecturer_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('lecturer.dashboard'))
    form = LecturerLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('lecturer.dashboard'))
        else:
            flash('Invalid name or password.', 'danger')
    return render_template('lecturer_login.html', form=form)

@lecturer_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('lecturer.login'))

@lecturer_bp.route('/dashboard')
@login_required
def dashboard():
    posts = Post.query.filter_by(subject=current_user.subject, status='active').order_by(Post.created_at.desc()).all()
    return render_template('lecturer_dashboard.html', posts=posts)

@lecturer_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.subject != current_user.subject:
        abort(403)

    # Chat
    chat_form = ChatMessageForm()
    if chat_form.validate_on_submit() and 'chat_submit' in request.form:
        msg = ChatMessage(
            post_id=post.id,
            lecturer_id=current_user.id,
            message=chat_form.message.data
        )
        db.session.add(msg)
        db.session.commit()
        flash('Message sent.', 'success')
        return redirect(url_for('lecturer.view_post', post_id=post.id))

    # Vote
    vote_form = VoteForm()
    if vote_form.validate_on_submit() and 'vote_submit' in request.form:
        # Check if NUMERICAL and value is required
        if vote_form.option.data == 'NUMERICAL' and vote_form.numerical_value.data is None:
            flash('Please enter a numerical value for NUMERICAL vote.', 'danger')
            return redirect(url_for('lecturer.view_post', post_id=post.id))

        existing_vote = Vote.query.filter_by(post_id=post.id, lecturer_id=current_user.id).first()
        if existing_vote:
            # Update existing vote
            existing_vote.option = vote_form.option.data
            existing_vote.numerical_value = vote_form.numerical_value.data
            db.session.commit()
            flash('Your vote has been updated.', 'success')
        else:
            # New vote
            vote = Vote(
                post_id=post.id,
                lecturer_id=current_user.id,
                option=vote_form.option.data,
                numerical_value=vote_form.numerical_value.data
            )
            db.session.add(vote)
            db.session.commit()
            flash('Your vote has been recorded.', 'success')
        return redirect(url_for('lecturer.view_post', post_id=post.id))

    current_vote = Vote.query.filter_by(post_id=post.id, lecturer_id=current_user.id).first()
    messages = ChatMessage.query.filter_by(post_id=post.id).order_by(ChatMessage.created_at.asc()).all()

    # Pre-populate vote form if current vote exists
    if current_vote:
        vote_form.option.data = current_vote.option
        vote_form.numerical_value.data = current_vote.numerical_value

    return render_template('lecturer_post.html',
                           post=post,
                           chat_form=chat_form,
                           vote_form=vote_form,
                           current_vote=current_vote,
                           messages=messages)