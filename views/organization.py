from flask import Blueprint,jsonify,request
from services import org_service, user_service
from utils.response_utils import success_response
from flask_jwt_extended import jwt_required, get_jwt_identity
org_bp = Blueprint('org', __name__, url_prefix='/org')

@org_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    current_user = get_jwt_identity()
    my_org_id = user_service.find_user(current_user)['org_id']
    # print("my org id:",my_org_id)
    result = org_service.query_all_node(my_org_id)
    # print(result)
    return jsonify(success_response(data=result,path=request.url))