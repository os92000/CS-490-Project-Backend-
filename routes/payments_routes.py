from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, CoachRelationship, CoachPricing, PaymentRecord
from utils.helpers import success_response, error_response
from utils.validators import validate_card_info
from datetime import datetime
import secrets
import json

payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payments_bp.route('/pricing/<int:coach_id>', methods=['GET'])
@jwt_required()
def get_coach_pricing(coach_id):
    """Get pricing for a coach"""
    try:
        pricing = CoachPricing.query.filter_by(coach_id=coach_id).all()
        return success_response({
            'pricing': [p.to_dict() for p in pricing]
        }, 'Pricing retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve pricing', 500, str(e))

@payments_bp.route('/process', methods=['POST'])
@jwt_required()
def process_payment():
    """Process payment (mock implementation)"""
    user_id = int(get_jwt_identity())
    data = request.get_json()

    try:
        # Minimal validation
        if not data:
            return error_response('Missing request body', 400)

        amount = data.get('amount')
        currency = data.get('currency', 'USD')
        coach_id = data.get('coach_id')
        card = data.get('card')

        if amount is None:
            return error_response('Amount is required', 400)
        try:
            amount = float(amount)
        except Exception:
            return error_response('Invalid amount', 400)
        if amount <= 0:
            return error_response('Amount must be positive', 400)

        # Validate card details (mock - do not store sensitive data)
        ok, card_meta = validate_card_info(card)
        if not ok:
            return error_response(f'Invalid card: {card_meta}', 400)

        # Create a payment record (mock processing)
        payment_reference = 'mock_' + secrets.token_hex(12)

        metadata = {
            'card': {
                'brand': card_meta.get('brand'),
                'last4': card_meta.get('last4'),
                'exp_month': card_meta.get('exp_month'),
                'exp_year': card_meta.get('exp_year'),
            }
        }
        # Optional additional metadata from the request
        for m in ('description', 'package'):
            if m in data:
                metadata[m] = data[m]

        payment = PaymentRecord(
            payer_id=user_id,
            coach_id=coach_id,
            payment_reference=payment_reference,
            amount=amount,
            currency=currency,
            status='completed',
            metadata_json=json.dumps(metadata),
            created_at=datetime.utcnow(),
        )
        db.session.add(payment)
        db.session.commit()

        return success_response({
            'payment': payment.to_dict()
        }, 'Payment processed (mock) and recorded', 200)
    except Exception as e:
        return error_response('Payment processing failed', 500, str(e))

@payments_bp.route('/history', methods=['GET'])
@jwt_required()
def payment_history():
    """Get payment history (mock implementation)"""
    user_id = int(get_jwt_identity())

    try:
        # Return payment records where user is payer or coach (received)
        payments = PaymentRecord.query.filter(
            db.or_(PaymentRecord.payer_id == user_id, PaymentRecord.coach_id == user_id)
        ).order_by(PaymentRecord.created_at.desc()).all()

        return success_response({
            'payments': [p.to_dict() for p in payments]
        }, 'Payment history retrieved', 200)
    except Exception as e:
        return error_response('Failed to retrieve payment history', 500, str(e))
