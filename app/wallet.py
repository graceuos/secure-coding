from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from app import db
from app.models import User, Transaction

wallet_bp = Blueprint('wallet', __name__)

class TransferForm(FlaskForm):
    amount = IntegerField('송금액', validators=[DataRequired(), NumberRange(min=1, max=100000000)])
    submit = SubmitField('송금하기')

@wallet_bp.route('/transfer/<int:user_id>', methods=['GET', 'POST'])
@login_required
def transfer(user_id):
    receiver = User.query.get_or_404(user_id)
    if receiver.id == current_user.id:
        abort(400)
    form = TransferForm()
    if form.validate_on_submit():
        amount = form.amount.data
        # 보안 포인트 23: 서버측에서 잔액 재확인 (클라이언트 조작값 신뢰 안 함)
        sender = User.query.get(current_user.id)
        if sender.balance < amount:
            flash('잔액이 부족합니다.')
            return redirect(url_for('wallet.transfer', user_id=user_id))
        sender.balance -= amount
        receiver.balance += amount
        tx = Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amount)
        db.session.add(tx)
        db.session.commit()
        flash(f'{receiver.username}님에게 {amount}원을 송금했습니다.')
        return redirect(url_for('users.user_profile', user_id=receiver.id))
    return render_template('transfer_form.html', form=form, receiver=receiver)