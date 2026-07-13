from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from app import db
from app.models import User, Product

users_bp = Blueprint('users', __name__)

@users_bp.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    products = Product.query.filter_by(seller_id=user.id, is_blocked=False).all()
    return render_template('user_profile.html', profile_user=user, products=products)

@users_bp.route('/my/products')
@login_required
def my_products():
    items = Product.query.filter_by(seller_id=current_user.id).order_by(Product.created_at.desc()).all()
    return render_template('my_products.html', items=items)

class ProductEditForm(FlaskForm):
    title = StringField('상품명', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('설명', validators=[Length(max=1000)])
    price = IntegerField('가격', validators=[DataRequired(), NumberRange(min=0, max=100000000)])
    submit = SubmitField('수정하기')

@users_bp.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    # 보안 포인트 19: 소유권 검증 - 본인 상품만 수정 가능
    if product.seller_id != current_user.id:
        abort(403)
    form = ProductEditForm(obj=product)
    if form.validate_on_submit():
        product.title = form.title.data
        product.description = form.description.data
        product.price = form.price.data
        db.session.commit()
        flash('상품 정보가 수정되었습니다.')
        return redirect(url_for('products.product_detail', product_id=product.id))
    return render_template('product_edit.html', form=form, product=product)