"""API routes."""

from flask import Blueprint, request, jsonify, session
from backend.services.auth_service import AuthService
from backend.services.aws_service import AWSService

api = Blueprint('api', __name__)
auth_service = AuthService()
aws_service = AWSService()

@api.route('/auth/register', methods=['POST'])
def register():
    data = request.json
    success, error = auth_service.register(
        data['username'], 
        data['email'], 
        data['password']
    )
    return jsonify({'success': success, 'error': error})

@api.route('/auth/login', methods=['POST'])
def login():
    data = request.json
    success, user = auth_service.login(data['username'], data['password'])
    
    if success:
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['patient_id'] = user['patient_id']
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'})

@api.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@api.route('/documents/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file'}), 400
    
    doc_id, text = aws_service.save_document(
        session['user_id'],
        session['patient_id'],
        file.filename,
        file.read()
    )
    
    if doc_id:
        return jsonify({'success': True, 'doc_id': doc_id, 'text': text[:500]})
    return jsonify({'error': text}), 400

@api.route('/documents/list', methods=['GET'])
def list_documents():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    docs = aws_service.get_user_documents(session['user_id'])
    return jsonify({
        'documents': [{
            'id': d['document_id'],
            'name': d['file_name'],
            'date': d['upload_timestamp'][:10]
        } for d in docs]
    })

@api.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    message = request.json.get('message')
    response = aws_service.chat_with_context(message, session['user_id'])
    return jsonify({'response': response})
