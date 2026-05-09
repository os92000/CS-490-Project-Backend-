import json
from flask_jwt_extended import create_access_token
from models import db, User, PaymentRecord


def test_validate_card_info_import():
    from utils.validators import validate_card_info

    ok, meta = validate_card_info({
        'number': '4242424242424242',
        'exp_month': 12,
        'exp_year': 2099,
        'cvc': '123'
    })
    assert ok is True
    assert meta.get('last4') == '4242'


def test_process_payment_creates_record(client, app):
    # create a user
    with app.app_context():
        user = User(email='tester.pay@local', role='client', status='active')
        user.set_password('Password123')
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))

    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    payload = {
        'amount': 49.00,
        'currency': 'USD',
        'card': {
            'number': '4242424242424242',
            'exp_month': 12,
            'exp_year': 2099,
            'cvc': '123'
        }
    }

    resp = client.post('/api/payments/process', data=json.dumps(payload), headers=headers)
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is True

    with app.app_context():
        recs = PaymentRecord.query.filter_by(payer_id=user.id).all()
        assert len(recs) == 1
        assert float(recs[0].amount) == 49.0
