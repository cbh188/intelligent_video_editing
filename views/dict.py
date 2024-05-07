from flask import Blueprint,jsonify,request
from services import dict_service
from utils.response_utils import success_response
from flask_jwt_extended import jwt_required

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
            result.append({"name": dict['name'], "detail": detail})
        else:
            detail = ""
            result.append({"name": dict['name'], "detail": detail})
    return jsonify(success_response(data=result,path=request.path))