from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from app import db
from app.models import User, Product, Report

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # 보안 포인트 24: 관리자 권한 검증, 아니면 무조건 403
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    users = User.query.order_by(User.id.asc()).all()
    products = Product.query.order_by(Product.id.asc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).limit(50).all()
    return render_template('admin_dashboard.html', users=users, products=products, reports=reports)

@admin_bp.route('/user/<int:user_id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f'{user.username} 계정 상태 변경됨.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/product/<int:product_id>/toggle_block', methods=['POST'])
@login_required
@admin_required
def toggle_product_block(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_blocked = not product.is_blocked
    db.session.commit()
    flash(f'{product.title} 상품 상태 변경됨.')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('상품이 삭제되었습니다.')
    return redirect(url_for('admin.dashboard'))