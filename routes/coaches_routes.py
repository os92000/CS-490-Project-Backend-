from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProfile, CoachSurvey, CoachSpecialization, Specialization, CoachAvailability, CoachPricing, ClientRequest, CoachRelationship, Review
from utils.helpers import success_response, error_response
from sqlalchemy import func, or_

coaches_bp = Blueprint('coaches', __name__, url_prefix='/api/coaches')

@coaches_bp.route('', methods=['GET'])
@jwt_required()
def get_coaches():
    """
    Browse/Search coaches (UC 2.1)
    GET /api/coaches?search=query&specialization=id&page=1&per_page=20
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '', type=str)
        specialization_id = request.args.get('specialization', type=int)

        # Base query: users who are coaches or both
        query = User.query.filter(or_(User.role == 'coach', User.role == 'both'))
        query = query.filter(User.status == 'active')

        # Join with profile for search
        if search:
            search_term = f'%{search}%'
            query = query.join(UserProfile).filter(
                or_(
                    UserProfile.first_name.ilike(search_term),
                    UserProfile.last_name.ilike(search_term),
                    UserProfile.bio.ilike(search_term)
                )
            )

        # Filter by specialization
        if specialization_id:
            query = query.join(CoachSpecialization).filter(
                CoachSpecialization.specialization_id == specialization_id
            )

        # Paginate
        paginated = query.paginate(page=page, per_page=min(per_page, 100), error_out=False)

        # Build coach data with ratings
        coaches = []
        for user in paginated.items:
            try:
                coach_data = user.to_dict(include_profile=True)

                # Add coach survey info
                coach_survey = CoachSurvey.query.filter_by(user_id=user.id).first()
                if coach_survey:
                    coach_data['coach_info'] = coach_survey.to_dict()
                else:
                    coach_data['coach_info'] = None

                # Add specializations
                specializations = CoachSpecialization.query.filter_by(coach_id=user.id).all()
                coach_data['specializations'] = [cs.to_dict() for cs in specializations]

                # Calculate average rating
                avg_rating = db.session.query(func.avg(Review.rating)).filter_by(coach_id=user.id).scalar()
                review_count = Review.query.filter_by(coach_id=user.id).count()
                coach_data['rating'] = {
                    'average': float(avg_rating) if avg_rating else 0,
                    'count': review_count
                }

                # Add pricing (first available pricing)
                pricing = CoachPricing.query.filter_by(coach_id=user.id).first()
                if pricing:
                    coach_data['pricing'] = pricing.to_dict()
                else:
                    coach_data['pricing'] = None

                coaches.append(coach_data)
            except Exception as coach_error:
                # Skip coaches with errors but log them
                print(f"Error loading coach {user.id}: {str(coach_error)}")
                continue

        return success_response({
            'coaches': coaches,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page,
            'per_page': per_page
        }, 'Coaches retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve coaches', 500, str(e))


@coaches_bp.route('/<int:coach_id>', methods=['GET'])
@jwt_required()
def get_coach_details(coach_id):
    """
    Get detailed coach profile (UC 2.2)
    GET /api/coaches/{coach_id}
    """
    try:
        coach = User.query.get(coach_id)

        if not coach:
            return error_response('Coach not found', 404)

        if coach.role not in ['coach', 'both']:
            return error_response('User is not a coach', 400)

        # Build detailed coach data
        coach_data = coach.to_dict(include_profile=True)

        # Add coach survey info
        coach_survey = CoachSurvey.query.filter_by(user_id=coach_id).first()
        if coach_survey:
            coach_data['coach_info'] = coach_survey.to_dict()
        else:
            coach_data['coach_info'] = None

        # Add specializations
        specializations = CoachSpecialization.query.filter_by(coach_id=coach_id).all()
        coach_data['specializations'] = [cs.to_dict() for cs in specializations]

        # Add availability
        availability = CoachAvailability.query.filter_by(coach_id=coach_id).all()
        coach_data['availability'] = [a.to_dict() for a in availability]

        # Add pricing
        pricing = CoachPricing.query.filter_by(coach_id=coach_id).all()
        coach_data['pricing'] = [p.to_dict() for p in pricing]

        # Calculate ratings
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(coach_id=coach_id).scalar()
        review_count = Review.query.filter_by(coach_id=coach_id).count()
        coach_data['rating'] = {
            'average': float(avg_rating) if avg_rating else 0,
            'count': review_count
        }

        return success_response(coach_data, 'Coach details retrieved successfully', 200)

    except Exception as e:
        print(f"Error loading coach details for {coach_id}: {str(e)}")
        return error_response('Failed to retrieve coach details', 500, str(e))


@coaches_bp.route('/<int:coach_id>/reviews', methods=['GET'])
@jwt_required()
def get_coach_reviews(coach_id):
    """
    Get reviews for a coach (UC 2.6)
    GET /api/coaches/{coach_id}/reviews?page=1&per_page=10
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Check if coach exists
        coach = User.query.get(coach_id)
        if not coach:
            return error_response('Coach not found', 404)

        # Get reviews with pagination
        paginated = Review.query.filter_by(coach_id=coach_id)\
            .order_by(Review.created_at.desc())\
            .paginate(page=page, per_page=min(per_page, 50), error_out=False)

        reviews = [review.to_dict(include_client=True) for review in paginated.items]

        return success_response({
            'reviews': reviews,
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': paginated.page
        }, 'Reviews retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve reviews', 500, str(e))


@coaches_bp.route('/<int:coach_id>/hire', methods=['POST'])
@jwt_required()
def send_hire_request(coach_id):
    """
    Send hire request to a coach (UC 2.3)
    POST /api/coaches/{coach_id}/hire
    """
    try:
        client_id = int(get_jwt_identity())

        # Validate coach exists
        coach = User.query.get(coach_id)
        if not coach:
            return error_response('Coach not found', 404)

        if coach.role not in ['coach', 'both']:
            return error_response('User is not a coach', 400)

        # Check if client already has an active relationship
        existing_relationship = CoachRelationship.query.filter_by(
            client_id=client_id,
            status='active'
        ).first()

        if existing_relationship:
            return error_response('You already have an active coach', 400)

        # Check if there's already a pending request
        existing_request = ClientRequest.query.filter_by(
            client_id=client_id,
            coach_id=coach_id,
            status='pending'
        ).first()

        if existing_request:
            return error_response('You already have a pending request to this coach', 400)

        # Create new request (auto-accepted)
        new_request = ClientRequest(
            client_id=client_id,
            coach_id=coach_id,
            status='accepted',
            responded_at=db.func.current_timestamp()
        )

        # Automatically create active relationship
        relationship = CoachRelationship(
            client_id=client_id,
            coach_id=coach_id,
            status='active'
        )

        db.session.add(new_request)
        db.session.add(relationship)
        db.session.commit()

        return success_response({
            'request': new_request.to_dict(),
            'relationship': relationship.to_dict()
        }, 'Coach hired successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to send hire request', 500, str(e))


@coaches_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_my_requests():
    """
    Get hire requests (for coaches) or sent requests (for clients)
    GET /api/coaches/requests?type=received|sent
    """
    try:
        user_id = int(get_jwt_identity())
        request_type = request.args.get('type', 'received', type=str)

        if request_type == 'received':
            # Get requests received as a coach
            requests = ClientRequest.query.filter_by(coach_id=user_id)\
                .order_by(ClientRequest.requested_at.desc()).all()
        else:
            # Get requests sent as a client
            requests = ClientRequest.query.filter_by(client_id=user_id)\
                .order_by(ClientRequest.requested_at.desc()).all()

        # Include user info
        requests_data = []
        for req in requests:
            req_dict = req.to_dict()
            if request_type == 'received':
                req_dict['client'] = req.client.to_dict(include_profile=True)
            else:
                req_dict['coach'] = req.coach.to_dict(include_profile=True)
            requests_data.append(req_dict)

        return success_response({
            'requests': requests_data
        }, 'Requests retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve requests', 500, str(e))


@coaches_bp.route('/requests/<int:request_id>', methods=['PATCH'])
@jwt_required()
def respond_to_request(request_id):
    """
    Accept or deny a hire request (UC 2.4)
    PATCH /api/coaches/requests/{request_id}
    Body: {status: 'accepted' | 'denied'}
    """
    try:
        coach_id = int(get_jwt_identity())
        data = request.get_json()

        if not data or 'status' not in data:
            return error_response('Status is required', 400)

        status = data['status']
        if status not in ['accepted', 'denied']:
            return error_response('Invalid status. Must be: accepted or denied', 400)

        # Get the request
        hire_request = ClientRequest.query.get(request_id)
        if not hire_request:
            return error_response('Request not found', 404)

        # Verify coach owns this request
        if hire_request.coach_id != coach_id:
            return error_response('Unauthorized to respond to this request', 403)

        if hire_request.status != 'pending':
            return error_response('Request has already been responded to', 400)

        # Update request status
        hire_request.status = status
        hire_request.responded_at = db.func.current_timestamp()

        # If accepted, create relationship
        if status == 'accepted':
            relationship = CoachRelationship(
                client_id=hire_request.client_id,
                coach_id=coach_id,
                status='active'
            )
            db.session.add(relationship)

        db.session.commit()

        return success_response(hire_request.to_dict(),
                              f'Request {status} successfully', 200)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to respond to request', 500, str(e))


@coaches_bp.route('/<int:coach_id>/review', methods=['POST'])
@jwt_required()
def submit_review(coach_id):
    """
    Submit a review for a coach (UC 2.5)
    POST /api/coaches/{coach_id}/review
    Body: {rating: 1-5, comment: string}
    """
    try:
        client_id = int(get_jwt_identity())
        data = request.get_json()

        # Validate required fields
        if not data or 'rating' not in data:
            return error_response('Rating is required', 400)

        rating = data['rating']
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return error_response('Rating must be between 1 and 5', 400)

        # Verify coach exists
        coach = User.query.get(coach_id)
        if not coach:
            return error_response('Coach not found', 404)

        # Verify client has/had a relationship with this coach
        relationship = CoachRelationship.query.filter_by(
            client_id=client_id,
            coach_id=coach_id
        ).first()

        if not relationship:
            return error_response('You must have a relationship with this coach to leave a review', 403)

        # Check if already reviewed
        existing_review = Review.query.filter_by(
            client_id=client_id,
            coach_id=coach_id
        ).first()

        if existing_review:
            return error_response('You have already reviewed this coach', 400)

        # Create review
        review = Review(
            client_id=client_id,
            coach_id=coach_id,
            rating=rating,
            comment=data.get('comment', '')
        )

        db.session.add(review)
        db.session.commit()

        return success_response(review.to_dict(), 'Review submitted successfully', 201)

    except Exception as e:
        db.session.rollback()
        return error_response('Failed to submit review', 500, str(e))


@coaches_bp.route('/specializations', methods=['GET'])
@jwt_required()
def get_specializations():
    """
    Get all available specializations
    GET /api/coaches/specializations
    """
    try:
        specializations = Specialization.query.all()
        return success_response({
            'specializations': [s.to_dict() for s in specializations]
        }, 'Specializations retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve specializations', 500, str(e))


@coaches_bp.route('/my-clients', methods=['GET'])
@jwt_required()
def get_my_clients():
    """
    Get coach's active clients
    GET /api/coaches/my-clients
    """
    try:
        coach_id = int(get_jwt_identity())

        # Get active relationships
        relationships = CoachRelationship.query.filter_by(
            coach_id=coach_id,
            status='active'
        ).all()

        clients = []
        for rel in relationships:
            client_data = rel.client.to_dict(include_profile=True)
            client_data['relationship_id'] = rel.id
            client_data['start_date'] = rel.start_date.isoformat() if rel.start_date else None
            clients.append(client_data)

        return success_response({
            'clients': clients
        }, 'Clients retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve clients', 500, str(e))


@coaches_bp.route('/my-coach', methods=['GET'])
@jwt_required()
def get_my_coach():
    """
    Get client's current coach
    GET /api/coaches/my-coach
    """
    try:
        client_id = int(get_jwt_identity())

        # Get active relationship
        relationship = CoachRelationship.query.filter_by(
            client_id=client_id,
            status='active'
        ).first()

        if not relationship:
            return error_response('No active coach found', 404)

        coach_data = relationship.coach.to_dict(include_profile=True)
        coach_data['relationship_id'] = relationship.id
        coach_data['start_date'] = relationship.start_date.isoformat() if relationship.start_date else None

        # Add coach survey info
        coach_survey = CoachSurvey.query.filter_by(user_id=relationship.coach.id).first()
        if coach_survey:
            coach_data['coach_info'] = coach_survey.to_dict()
        else:
            coach_data['coach_info'] = None

        return success_response(coach_data, 'Coach retrieved successfully', 200)

    except Exception as e:
        return error_response('Failed to retrieve coach', 500, str(e))
