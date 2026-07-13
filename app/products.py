from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

from app import db
from app.models import Product

products_bp = Blueprint('products', __name__)

class ProductForm(FlaskForm):
    # 보안 포인트 7: 서버 측 검증 - 가격은 0 이상 정수만 허용 (음수/이상값 차단)
    title = StringField('상품명', validators=[DataRequired(), Length(min=1, max=100)])
    description = TextAreaField('설명', validators=[Length(max=1000)])
    price = IntegerField('가격', validators=[DataRequired(), NumberRange(min=0, max=100000000)])
    submit = SubmitField('등록하기')

@products_bp.route('/')
@login_required
def product_list():
    # 보안 포인트 8: 차단된(is_blocked) 상품은 목록에서 제외하여 노출 방지
    items = Product.query.filter_by(is_blocked=False).order_by(Product.created_at.desc()).all()
    return render_template('product_list.html', items=items)

@products_bp.route('/product/new', methods=['GET', 'POST'])
@login_required
def product_new():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            seller_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        flash('상품이 등록되었습니다.')
        return redirect(url_for('products.product_list'))
    return render_template('product_new.html', form=form)

@products_bp.route('/product/<int:product_id>')
@login_required
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # 보안 포인트 9: 차단된 상품은 본인 것이 아니면 볼 수 없게 처리
    if product.is_blocked and product.seller_id != current_user.id:
        abort(404)
    return render_template('product_detail.html', product=product)

@products_bp.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    # 보안 포인트 10: 소유권 검증 - 본인 상품만 삭제 가능 (남의 상품 삭제 방지)
    if product.seller_id != current_user.id:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('상품이 삭제되었습니다.')
    return redirect(url_for('products.product_list'))
