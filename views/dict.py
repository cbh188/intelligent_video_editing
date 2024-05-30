from datetime import datetime

from flask import Blueprint,jsonify,request
from services import dict_service, user_service, base_service
from utils.response_utils import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity

dict_bp = Blueprint('dict_bp', __name__,url_prefix='/dict')

@dict_bp.route('/getDicts', methods=['GET'])
@jwt_required()
def get_dicts():
    dict_name = request.args.get('dictName')
    dicts = dict_service.get_dicts_by_pname(dict_name)
    results = []
    for dict in dicts:
        results.append({"label": dict['name'],"value": int(dict['num'])})
    # print(results)
    return jsonify(success_response(data=results,path=request.path))

@dict_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    name = request.args.get('name')
    if name is not None:
        dict_list = dict_service.find_by_name_like(name)
        # return jsonify(success_response(data=dict_list,path=request.path))
    else:
        dict_list = dict_service.find_by_pid(0)
        # return jsonify(success_response(data=dict_list,path=request.path))
    result = []
    for dict in dict_list:
        if dict['pid'] == 0:
            sub_dict_list = dict_service.find_by_pid(dict['id'])
            detail = ""
            for sub_dict in sub_dict_list:
                detail += sub_dict['num']+":" + sub_dict['name']+","
            detail = detail[:-1]
            # print(detail)
            result.append({"id": dict['id'], "name": dict['name'], "detail": detail})
        else:
            detail = ""
            result.append({"id": dict['id'], "name": dict['name'], "detail": detail})
    print(result)
    return jsonify(success_response(data=result,path=request.path))

@dict_bp.route('', methods=['POST'])
@jwt_required()
def add_dict():
    dict_name = request.json.get('name')
    dict_values = request.json.get('detail')
    current_user = get_jwt_identity()
    user_id = user_service.find_user(current_user)['user_id']

    # 判断有没有该字典
    dicts = dict_service.find_by_name_pid(dict_name, 0)
    if dicts is not None and len(dicts) > 0:
        return error_response(400, 40001, "该字典已存在", "该字典已存在")

    dict_service.add_dict(dict_name, dict_values, user_id)

    return success_response(data=None, path=request.path)

@dict_bp.route('', methods=['PUT'])
@jwt_required()
def update_dict():
    dict_id = request.json.get('id')
    dict_name = request.json.get('name')
    dict_values = request.json.get('detail')
    current_user = get_jwt_identity()
    user_id = user_service.find_user(current_user)['user_id']
    # 删除之前的字典
    dict_service.delete_dict(dict_id)

    # 重新添加新的字典
    dict_service.add_dict(dict_name, dict_values, user_id)

    return success_response(data=None, path=request.path)

@dict_bp.route('', methods=['DELETE'])
@jwt_required()
def delete_dict():
    dict_ids = request.args.getlist('id[]')
    print(dict_ids)
    if dict_ids is None:
        return error_response(400, 40001, "不能为空", "请选择要删除的字典")
    if dict_service.delete_dict(dict_ids) > 0:
        return success_response(data=None, path=request.path)