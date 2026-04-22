from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from models import db, User, CoachRelationship, ChatMessage, ModerationReport
from utils.helpers import success_response, error_response
from datetime import datetime

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

# Holds the SocketIO instance once init_socketio_events is called
_socketio = None

# Store active socket connections
active_users = {}

@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """
    Get all conversations for the current user
    GET /api/chat/conversations
    """
    try:
        user_id = int(get_jwt_identity())

        # Get relationships where user is either client or coach
        relationships = CoachRelationship.query.filter(
            db.or_(
                CoachRelationship.client_id == user_id,
                CoachRelationship.coach_id == user_id
            ),
            CoachRelationship.status == 'active'
        ).all()

        conversations = []
        for rel in relationships:
            # Determine the other user in the conversation
            if rel.client_id == user_id:
                other_user = rel.coach
                other_user_type = 'coach'
            else:
                other_user = rel.client
                other_user_type = 'client'

            # Get last message
            last_message = ChatMessage.query.filter_by(relationship_id=rel.id)\
                .order_by(ChatMessage.sent_at.desc()).first()

            # Count unread messages
            unread_count = ChatMessage.query.filter_by(
                relationship_id=rel.id,
                read_at=None
            ).filter(ChatMessage.sender_id != user_id).count()

            conversations.append({
                'relationship_id': rel.id,
                'other_user': {
                    'id': other_user.id,
                    'email': other_user.email,
                    'type': other_user_type,
                    'profile': other_user.profile.to_dict() if other_user.profile else None
                },
                'last_message': last_message.to_dict() if last_message else None,
                'unread_count': unread_count
            })

        return success_response({
            'conversations': conversations
        }, 'Conversations retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve conversations', 500, str(e))


@chat_bp.route('/messages/<int:relationship_id>', methods=['GET'])
@jwt_required()
def get_messages(relationship_id):
    """
    Get messages for a specific conversation
    GET /api/chat/messages/{relationship_id}?page=1&per_page=50
    """
    try:
        user_id = int(get_jwt_identity())
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)

        # Verify user is part of this relationship
        relationship = CoachRelationship.query.get(relationship_id)
        if not relationship:
            return error_response('Relationship not found', 404)

        if relationship.client_id != user_id and relationship.coach_id != user_id:
            return error_response('Unauthorized to access this conversation', 403)

        # Get messages with pagination
        paginated = ChatMessage.query.filter_by(relationship_id=relationship_id)\
            .order_by(ChatMessage.sent_at.desc())\
            .paginate(page=page, per_page=min(per_page, 100), error_out=False)

        messages = [msg.to_dict(include_sender=True) for msg in reversed(paginated.items)]

        # Mark messages as read
        unread_messages = ChatMessage.query.filter_by(
            relationship_id=relationship_id,
            read_at=None
        ).filter(ChatMessage.sender_id != user_id).all()

        for msg in unread_messages:
            msg.read_at = datetime.utcnow()

        if unread_messages:
            db.session.commit()

        return success_response({
            'messages': messages,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page
        }, 'Messages retrieved successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to retrieve messages', 500, str(e))


@chat_bp.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    """
    Send a message (REST endpoint for compatibility)
    POST /api/chat/messages
    Body: {relationship_id, message}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'relationship_id' not in data or 'message' not in data:
            return error_response('relationship_id and message are required', 400)

        relationship_id = data['relationship_id']
        message_text = data['message'].strip()

        if not message_text:
            return error_response('Message cannot be empty', 400)

        # Verify user is part of this relationship
        relationship = CoachRelationship.query.get(relationship_id)
        if not relationship:
            return error_response('Relationship not found', 404)

        if relationship.client_id != user_id and relationship.coach_id != user_id:
            return error_response('Unauthorized to send messages in this conversation', 403)

        # Create message
        message = ChatMessage(
            relationship_id=relationship_id,
            sender_id=user_id,
            message=message_text
        )

        db.session.add(message)
        db.session.commit()

        message_data = message.to_dict(include_sender=True)

        if _socketio:
            recipient_id = (
                relationship.coach_id if relationship.client_id == user_id
                else relationship.client_id
            )
            _socketio.emit('new_message', message_data, to=f'conversation_{relationship_id}')
            _socketio.emit('new_message', message_data, to=f'user_{recipient_id}')

        return success_response(message_data, 'Message sent successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to send message', 500, str(e))


@chat_bp.route('/reports', methods=['POST'])
@jwt_required()
def create_chat_report():
    """
    Report a chat conversation for admin review
    POST /api/chat/reports
    Body: {relationship_id, reason, details}
    """
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}

        if not data.get('relationship_id') or not data.get('reason'):
            return error_response('relationship_id and reason are required', 400)

        relationship = CoachRelationship.query.get(data['relationship_id'])
        if not relationship:
            return error_response('Relationship not found', 404)

        if relationship.client_id != user_id and relationship.coach_id != user_id:
            return error_response('Unauthorized to report this conversation', 403)

        report = ModerationReport(
            report_type='chat',
            reporter_id=user_id,
            reported_user_id=relationship.coach_id if relationship.client_id == user_id else relationship.client_id,
            relationship_id=relationship.id,
            reason=data['reason'],
            details=data.get('details')
        )
        db.session.add(report)
        db.session.commit()
        return success_response(report.to_dict(), 'Chat report submitted successfully', 201)
    except Exception as e:
        db.session.rollback()
        return error_response('Failed to report conversation', 500, str(e))


# WebSocket event handlers
def init_socketio_events(socketio):
    """Initialize Socket.IO event handlers"""
    global _socketio
    _socketio = socketio

    @socketio.on('connect')
    def handle_connect(auth):
        """Handle client connection"""
        print('Client connected:', request.sid)
        emit('connection_status', {'status': 'connected'})

    @socketio.on('register_user')
    def handle_register_user(data):
        """Join a personal room so the user receives messages for all their conversations"""
        user_id = data.get('user_id')
        if user_id:
            join_room(f'user_{user_id}')
            print(f'User {user_id} joined personal room')

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected:', request.sid)
        # Remove from active users
        for user_id, sid in list(active_users.items()):
            if sid == request.sid:
                del active_users[user_id]
                break

    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        """Join a conversation room"""
        try:
            relationship_id = data.get('relationship_id')
            user_id = data.get('user_id')

            if not relationship_id or not user_id:
                emit('error', {'message': 'Missing relationship_id or user_id'})
                return

            # Verify user is part of this relationship
            relationship = CoachRelationship.query.get(relationship_id)
            if not relationship:
                emit('error', {'message': 'Relationship not found'})
                return

            if relationship.client_id != user_id and relationship.coach_id != user_id:
                emit('error', {'message': 'Unauthorized'})
                return

            # Join the room
            room = f'conversation_{relationship_id}'
            join_room(room)
            active_users[user_id] = request.sid

            print(f'User {user_id} joined conversation {relationship_id}')
            emit('joined_conversation', {'relationship_id': relationship_id})

        except Exception as e:
            print('Error joining conversation:', str(e))
            emit('error', {'message': str(e)})

    @socketio.on('leave_conversation')
    def handle_leave_conversation(data):
        """Leave a conversation room"""
        try:
            relationship_id = data.get('relationship_id')

            if not relationship_id:
                return

            room = f'conversation_{relationship_id}'
            leave_room(room)

            print(f'User left conversation {relationship_id}')
            emit('left_conversation', {'relationship_id': relationship_id})

        except Exception as e:
            print('Error leaving conversation:', str(e))
            emit('error', {'message': str(e)})

    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle real-time message sending"""
        try:
            relationship_id = data.get('relationship_id')
            sender_id = data.get('sender_id')
            message_text = data.get('message', '').strip()

            if not all([relationship_id, sender_id, message_text]):
                emit('error', {'message': 'Missing required fields'})
                return

            # Verify user is part of this relationship
            relationship = CoachRelationship.query.get(relationship_id)
            if not relationship:
                emit('error', {'message': 'Relationship not found'})
                return

            if relationship.client_id != sender_id and relationship.coach_id != sender_id:
                emit('error', {'message': 'Unauthorized'})
                return

            # Create message
            message = ChatMessage(
                relationship_id=relationship_id,
                sender_id=sender_id,
                message=message_text
            )

            db.session.add(message)
            db.session.commit()

            # Get sender info
            sender = User.query.get(sender_id)
            message_data = message.to_dict()
            message_data['sender'] = {
                'id': sender.id,
                'email': sender.email,
                'profile': sender.profile.to_dict() if sender.profile else None
            }

            # Emit to all users in the conversation room and to the recipient's personal room
            room = f'conversation_{relationship_id}'
            emit('new_message', message_data, room=room, include_self=True)
            recipient_id = (
                relationship.coach_id if relationship.client_id == sender_id
                else relationship.client_id
            )
            emit('new_message', message_data, to=f'user_{recipient_id}')

            print(f'Message sent in conversation {relationship_id}')

        except Exception as e:
            db.session.rollback()
            print('Error sending message:', str(e))
            emit('error', {'message': str(e)})

    @socketio.on('mark_as_read')
    def handle_mark_as_read(data):
        """Mark messages as read"""
        try:
            relationship_id = data.get('relationship_id')
            user_id = data.get('user_id')

            if not relationship_id or not user_id:
                return

            # Mark all unread messages from other user as read
            unread_messages = ChatMessage.query.filter_by(
                relationship_id=relationship_id,
                read_at=None
            ).filter(ChatMessage.sender_id != user_id).all()

            for msg in unread_messages:
                msg.read_at = datetime.utcnow()

            if unread_messages:
                db.session.commit()

            emit('messages_marked_read', {
                'relationship_id': relationship_id,
                'count': len(unread_messages)
            })

        except Exception as e:
            db.session.rollback()
            print('Error marking messages as read:', str(e))
