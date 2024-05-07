from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services import base_service, menu_service
from utils.response_utils import success_response

menu_bp = Blueprint('menu', __name__, url_prefix='/menu')

@menu_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    menu_list = menu_service.get_menus()
    print(menu_list)
    return jsonify(success_response(data=menu_list, path=request.path))