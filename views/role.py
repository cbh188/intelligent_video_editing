from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, user_service, org_service
from utils.response_utils import success_response

role_bp = Blueprint('role', __name__, url_prefix='/role')

@role_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    name = request.args.get('name')
    code = request.args.get('code')
    org_id = request.args.get('orgId')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))

    query = f"""
                SELECT r1.role_id AS id,r1.name AS name,r1.code AS code,r1.org_id AS orgId,r1.num AS num,r1.gmt_create AS createTime,
                r1.pid AS pid, (CASE WHEN (r2.role_id = 0 OR r2.role_id IS NULL) THEN NULL ELSE r2.name END) AS pName
                FROM role r1 LEFT JOIN role r2 ON r1.pid = r2.role_id 
            """
    conditions = []
    params = []

    condition, param = base_service.build_fuzzy_search_conditions("r1.name", name)
    if condition:
        conditions.append(condition)
        params.append(param)

    if org_id is not None:
        conditions.append("r1.org_id = %s")
        params.append(org_id)

    if code is not None:
        conditions.append("r1.code = '%s'")
        params.append(str(code))

    current_user = get_jwt_identity()
    my_org_id = user_service.find_user(current_user)['org_id']
    org_list = org_service.query_all_sub(my_org_id)
    org_ids = []
    for org in org_list:
        org_ids.append(org['id'])
    query += " WHERE r1.org_id IN {}".format(tuple(org_ids))

    if conditions:
        query += " AND " + " AND ".join(conditions) + " ORDER BY r1.num ASC"

    query_with_params = query % tuple(params)
    print(query_with_params)
    roles = base_service.query_page(query_with_params,page_num,page_size)

    for role in roles:
        role['createTime'] = role['createTime'].strftime("%Y-%m-%d %H:%M:%S")

    result = {
        "list": roles,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": len(roles)
    }

    return jsonify(success_response(data=result, path=request.path))