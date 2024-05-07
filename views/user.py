from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.sql.functions import user

from services import user_service, base_service,org_service
from utils.response_utils import success_response
from utils.date_util import parse_time

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    account = request.args.get('account')
    name = request.args.get('name')
    org_id = request.args.get('org_id')
    phone = request.args.get('phone')
    status = request.args.get('status')
    sex = request.args.get('sex')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))
    # print(start_time)

    query = f"""
            SELECT user_id,name,account,org_id,sex,email,gmt_create,phone,status FROM user
        """
    conditions = []
    params = []

    condition, param = base_service.build_fuzzy_search_conditions("name", name)
    if condition:
        conditions.append(condition)
        params.append(param)

    condition, param = base_service.build_fuzzy_search_conditions("account", account)
    if condition:
        conditions.append(condition)
        params.append(param)

    if org_id is not None:
        conditions.append("org_id = '%s'")
        params.append(org_id)
    if phone:
        conditions.append("phone = '%s'")
        params.append(phone)
    if status is not None:
        conditions.append("status = '%s'")
        params.append(status)
    if sex is not None:
        conditions.append("sex = '%s'")
        params.append(sex)

    if start_time:
        start_time = parse_time(start_time)
        conditions.append("gmt_create >= '%s'")
        params.append(start_time)

    if end_time:
        end_time = parse_time(end_time)
        conditions.append("gmt_create <= '%s'")
        params.append(end_time)

    current_user = get_jwt_identity()
    my_org_id = user_service.find_user(current_user)['org_id']
    org_list = org_service.query_all_sub(my_org_id)
    org_ids = []
    for org in org_list:
        org_ids.append(org['id'])
    query += " WHERE org_id IN {}".format(tuple(org_ids))


    if conditions:
        query += " AND " + " AND ".join(conditions)

    query_with_params = query % tuple(params)
    # print(query_with_params)
    users = base_service.query_page(query_with_params, page_num, page_size)
    for user in users:
        user["gmt_create"] = user["gmt_create"].strftime("%Y-%m-%d %H:%M:%S")

    paginated_result = {
        "list": users,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": len(users)
    }
    print(paginated_result)
    return jsonify(success_response(data=paginated_result, path=request.path))

@user_bp.route("/getAllOrgs", methods=["GET"])
def get_all_orgs():
    result = org_service.query_all()
    return jsonify(success_response(data=result, path=request.path))
