from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

from app import db
from app.models import Report, User, Product

reports_bp = Blueprint('reports', __name__)

REPORT_THRESHOLD = 3  # 이 횟수 이상 신고되면 자동 차단/휴면

class ReportForm(FlaskForm):
	# 보안 포인트 15: 신고 사유는 필수 입력, 길이 제한 (요구사항: 신고 사유 작성 필수)
	reason = TextAreaField('신고 사유', validators=[DataRequired(), Length(min=1, max=500)])
	submit = SubmitField('신고하기')

@reports_bp.route('/report/product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def report_product(product_id):
	product = Product.query.get_or_404(product_id)
	# 보안 포인트 16: 본인 상품은 신고 불가
	if product.seller_id == current_user.id:
		abort(403)
	form = ReportForm()
	if form.validate_on_submit():
		report = Report(
			reporter_id=current_user.id,
			target_type='product',
			target_id=product.id,
			reason=form.reason.data
		)
		db.session.add(report)
		product.report_count += 1
		if product.report_count >= REPORT_THRESHOLD:
			product.is_blocked = True
		db.session.commit()
		flash('신고가 접수되었습니다.')
		return redirect(url_for('products.product_list'))
	return render_template('report_form.html', form=form, target_name=product.title)

@reports_bp.route('/report/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def report_user(user_id):
	target_user = User.query.get_or_404(user_id)
	# 보안 포인트 17: 본인 신고 불가
	if target_user.id == current_user.id:
		abort(403)
	form = ReportForm()
	if form.validate_on_submit():
		report = Report(
			reporter_id=current_user.id,
			target_type='user',
			target_id=target_user.id,
			reason=form.reason.data
		)
		db.session.add(report)
		target_user.report_count += 1
		if target_user.report_count >= REPORT_THRESHOLD:
			target_user.is_active_account = False
		db.session.commit()
		flash('신고가 접수되었습니다.')
		return redirect(url_for('products.product_list'))
	return render_template('report_form.html', form=form, target_name=target_user.username)

