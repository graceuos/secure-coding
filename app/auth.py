from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length

from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

class RegisterForm(FlaskForm):
    # 보안 포인트 4: 서버 측 입력값 길이 검증 (클라이언트 검증만 믿으면 안 됨)
    username = StringField('아이디', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField('가입하기')

class LoginForm(FlaskForm):
    username = StringField('아이디', validators=[DataRequired()])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    submit = SubmitField('로그인')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # 보안 포인트 5: 아이디 중복 체크 (요구사항: 아이디는 중복 안 됨)
        existing = User.query.filter_by(username=form.username.data).first()
        if existing:
            flash('이미 존재하는 아이디입니다.')
            return redirect(url_for('auth.register'))

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # 보안 포인트 6: 로그인 실패 메시지를 "아이디 없음"/"비번 틀림"으로 구분하지 않음
        # (구분해서 알려주면 공격자가 존재하는 아이디를 알아낼 수 있음 - 계정 열거 공격 방지)
        if user is None or not user.check_password(form.password.data):
            flash('아이디 또는 비밀번호가 올바르지 않습니다.')
            return redirect(url_for('auth.login'))
        if not user.is_active_account:
            flash('휴면 처리된 계정입니다.')
            return redirect(url_for('auth.login'))
        login_user(user)
        return redirect(url_for('auth.mypage'))
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/mypage')
@login_required
def mypage():
    return render_template('mypage.html', user=current_user)
