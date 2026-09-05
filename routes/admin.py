from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Post, Vote
from forms import AdminLoginForm
from extensions import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.username.data, is_admin=True).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Admin logged in.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
    return render_template('admin_login.html', form=form)

@admin_bp.route('/logout')
@login_required
def logout():
    if current_user.is_admin:
        logout_user()
        flash('Logged out.', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        abort(403)

    active_posts = Post.query.filter_by(status='active').order_by(Post.created_at.desc()).all()
    updated_posts = Post.query.filter_by(status='updated').order_by(Post.created_at.desc()).all()

    def get_vote_stats(post):
        # Count votes per option
        vote_counts = db.session.query(Vote.option, func.count(Vote.id)).filter(Vote.post_id == post.id).group_by(Vote.option).all()
        counts = {opt: 0 for opt in ['GRACE', '1', '2', '3', '4', 'NUMERICAL']}
        for opt, cnt in vote_counts:
            counts[opt] = cnt

        # Get numerical values for NUMERICAL votes
        numerical_values = db.session.query(Vote.numerical_value).filter(Vote.post_id == post.id, Vote.option == 'NUMERICAL').all()
        numerical_values = [v[0] for v in numerical_values if v[0] is not None]

        total_lecturers = User.query.filter_by(subject=post.subject, is_admin=False).count()
        voted_lecturers = Vote.query.filter_by(post_id=post.id).count()
        fraction = f"{voted_lecturers}/{total_lecturers}" if total_lecturers else "0/0"

        return counts, fraction, numerical_values

    active_data = [(post, *get_vote_stats(post)) for post in active_posts]
    updated_data = [(post, *get_vote_stats(post)) for post in updated_posts]

    return render_template('admin_dashboard.html',
                           active_data=active_data,
                           updated_data=updated_data)

@admin_bp.route('/mark-updated/<int:post_id>', methods=['POST'])
@login_required
def mark_updated(post_id):
    if not current_user.is_admin:
        abort(403)
    post = Post.query.get_or_404(post_id)
    post.status = 'updated'
    db.session.commit()
    flash(f'Post #{post.id} (JUT#{post.jut_number}) marked as updated.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    if not current_user.is_admin:
        abort(403)
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash(f'Post #{post.id} deleted permanently.', 'success')
    return redirect(url_for('admin.dashboard'))