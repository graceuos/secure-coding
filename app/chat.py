from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from flask_socketio import emit, join_room

from app import db, socketio
from app.models import Message, User, Product

chat_bp = Blueprint('chat', __name__)

def get_room_name(product_id, user_id_1, user_id_2):
    ids = sorted([user_id_1, user_id_2])
    return f"product_{product_id}_{ids[0]}_{ids[1]}"

@chat_bp.route('/chat/list')
@login_required
def chat_list():
    # 내가 보냈거나 받은 "상품 관련" 메시지들에서 (상품, 상대방) 조합을 뽑아냄
    msgs = Message.query.filter(
        Message.product_id.isnot(None),
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).all()

    seen = set()
    conversations = []
    for m in msgs:
        other_id = m.receiver_id if m.sender_id == current_user.id else m.sender_id
        key = (m.product_id, other_id)
        if key not in seen:
            seen.add(key)
            conversations.append({
                'product': m.product,
                'other': User.query.get(other_id)
            })
    return render_template('chat_list.html', conversations=conversations)

@chat_bp.route('/chat')
@login_required
def chat_global():
    history = Message.query.filter_by(receiver_id=None).order_by(Message.created_at.asc()).limit(100).all()
    return render_template('chat_global.html', history=history)

@chat_bp.route('/chat/product/<int:product_id>/<int:other_user_id>')
@login_required
def chat_private(product_id, other_user_id):
    product = Product.query.get_or_404(product_id)
    other = User.query.get_or_404(other_user_id)
    if other.id == current_user.id:
        abort(400)
    # 보안 포인트: 대화 당사자가 아니면(둘 중 하나는 반드시 판매자여야 함) 접근 차단
    if current_user.id != product.seller_id and other.id != product.seller_id:
        abort(403)

    room = get_room_name(product_id, current_user.id, other.id)
    history = Message.query.filter(
        Message.product_id == product_id,
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other.id)) |
        ((Message.sender_id == other.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc()).limit(100).all()
    return render_template('chat_private.html', other=other, product=product, room=room, history=history)


# ===== Socket.IO 이벤트 =====

@socketio.on('connect')
def handle_connect():
    if not current_user.is_authenticated:
        return False

@socketio.on('join')
def handle_join(data):
    room = data.get('room')
    if room:
        join_room(room)

@socketio.on('send_global_message')
def handle_global_message(data):
    if not current_user.is_authenticated:
        return
    content = (data.get('content') or '').strip()
    if not content or len(content) > 500:
        return
    msg = Message(sender_id=current_user.id, receiver_id=None, content=content)
    db.session.add(msg)
    db.session.commit()
    emit('receive_global_message', {
        'sender': current_user.username,
        'content': content,
        'time': msg.created_at.strftime('%H:%M')
    }, broadcast=True)

@socketio.on('send_private_message')
def handle_private_message(data):
    if not current_user.is_authenticated:
        return
    receiver_id = data.get('receiver_id')
    product_id = data.get('product_id')
    content = (data.get('content') or '').strip()
    if not content or len(content) > 500 or not receiver_id or not product_id:
        return
    receiver = User.query.get(receiver_id)
    product = Product.query.get(product_id)
    if not receiver or not product:
        return
    msg = Message(sender_id=current_user.id, receiver_id=receiver_id, product_id=product_id, content=content)
    db.session.add(msg)
    db.session.commit()
    room = get_room_name(product_id, current_user.id, receiver_id)
    emit('receive_private_message', {
        'sender': current_user.username,
        'content': content,
        'time': msg.created_at.strftime('%H:%M')
    }, room=room)
    