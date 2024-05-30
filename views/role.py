from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, user_service, org_service, role_service, account_service
from services.user_service import get_user_by_id
from utils.response_utils import success_response, error_response

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

    # current_user = get_jwt_identity()
    # my_org_id = user_service.find_user(current_user)['org_id']
    # org_list = org_service.query_all_sub(my_org_id)
    # org_ids = []
    # for org in org_list:
    #     org_ids.append(org['id'])
    # if len(org_ids) == 1:
    #     org_ids = f'({org_ids[0]})'
    # else:
    #     org_ids = tuple(org_ids)
    # query += " WHERE r1.org_id IN {}".format(org_ids)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY r1.num ASC"

    # if conditions:
    #     query += " AND " + " AND ".join(conditions) + " ORDER BY r1.num ASC"

    query_with_params = query % tuple(params)
    # print(query_with_params)
    roles = base_service.query_page(query_with_params,page_num,page_size)

    for role in roles:
        role['createTime'] = role['createTime'].strftime("%Y-%m-%d %H:%M:%S")
    # print(roles)
    result = {
        "list": roles,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": len(roles)
    }

    return jsonify(success_response(data=result, path=request.path))

# 获取用户角色列表
@role_bp.route('/roleListByIdUser', methods=['GET'])
@jwt_required()
def role_list_by_id_user():
    user_id = request.args.get('userId')
    user = get_user_by_id(user_id)
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    role_id = current_user['role_id']
    role_list = role_service.query_roles(role_id)
    listData = role_list
    checkedId = user['role_id']
    checkedRole = role_service.get_role_by_id(checkedId)
    checkedRoleName = checkedRole['name']
    return jsonify(success_response(data={"listData": listData, "checkedId": checkedId, "checkedRoleName": checkedRoleName}, path=request.path))

@role_bp.route('', methods=['POST'])
@jwt_required()
def save():
    role_id = request.json.get('id')
    code = request.json.get('code')
    name = request.json.get('name')
    org_id = request.json.get('orgId')
    num = request.json.get('num')
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    user_id = current_user['user_id']
    my_role = current_user['role_id']
    repeat_role = role_service.find_role_by_code(code)

    if role_id is None:
        if repeat_role is not None:
            return error_response(400, 40001, "角色编码重复", "角色编码重复")
        if num is None:
            return error_response(400, 40001, "角色排序不能为空", "角色排序不能为空")
        pid = my_role
        gmt_create = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        create_by = user_id
        sql = ("INSERT INTO role (code, name, org_id, num, pid, gmt_create, create_by) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        params = [code, name, org_id, num, pid, gmt_create, create_by]
        if base_service.insert(sql, params) > 0:
            return success_response(data=code, path=request.path)
    else:
        if repeat_role is not None and repeat_role['role_id'] != role_id:
            return error_response(400, 40001, "角色编码重复", "角色编码重复")
        gmt_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        modified_by = user_id
        sql = ("UPDATE role SET code = %s, name = %s, org_id = %s, num = %s, gmt_modified = %s, modified_by = %s "
               "WHERE role_id = %s")
        params = [code, name, org_id, num, gmt_modified, modified_by, role_id]
        if base_service.update(sql, params) >= 0:
            return success_response(data=None, path=request.path)

@role_bp.route('', methods=['DELETE'])
@jwt_required()
def remove():
    role_ids = request.args.getlist('id[]')
    role_ids = [int(role_id) for role_id in role_ids]
    current_user_account = get_jwt_identity()
    current_user = account_service.get_my_info(current_user_account)
    print(role_ids)
    for role_id in role_ids:
        if int(role_id) <= int(current_user["role_id"]):
            return error_response(400, 40001, "不能删除权限更高的角色", "不能删除权限更高的角色")
    if len(role_ids) == 1:
        sql = "DELETE FROM role WHERE role_id = {}".format(role_ids[0])
        sql_permission = "DELETE FROM role_rel_menu WHERE role_id = {}".format(role_ids[0])
    else:
        sql = "DELETE FROM role WHERE role_id IN {}".format(tuple(role_ids))
        sql_permission = "DELETE FROM role_rel_menu WHERE role_id IN {}".format(tuple(role_ids))
    base_service.delete(sql)
    # 删除角色所有权限
    base_service.delete(sql_permission)
    return success_response(data=None, path=request.path)

@role_bp.route('/savePermisson', methods=['POST'])
@jwt_required()
def save_permisson():
    role_id = request.json.get('roleId')
    permissions = request.json.get('permissions')
    # print(permissions)
    permission_list = permissions[:-1].split(',')
    # print(permission_list)

    # 先删除原先的权限
    sql = "DELETE FROM role_rel_menu WHERE role_id = {}".format(role_id)
    base_service.delete(sql)

    # 找到所有的pcodes
    if len(permission_list) == 1:
        sql = "SELECT DISTINCT pcodes FROM menu WHERE id = {}".format(permission_list[0])
    else:
        sql = "SELECT DISTINCT pcodes FROM menu WHERE id IN {}".format(tuple(permission_list))
    pcodes_list = base_service.query_all(sql)
    pcode_list = []
    # print(pcodes_list)
    for pcodes in pcodes_list:
        pcodes = pcodes['pcodes'][:-1]
        # print("pcodes_org: ",pcodes)
        pcodes = pcodes.split(',')
        pcodes = [item.strip('[]') for item in pcodes]
        # print(pcodes)
        for pcode in pcodes:
            if pcode not in pcode_list:
                pcode_list.append(pcode)
    # print(pcode_list)

    if pcode_list is not None:
        if len(pcode_list) == 1:
            sql = "SELECT id FROM menu WHERE code = {}".format(pcode_list[0])
        else:
            sql = "SELECT id FROM menu WHERE code IN {}".format(tuple(pcode_list))
    # print(sql)
    pids = base_service.query_all(sql)
    # print(pids)
    for pid in pids:
        if pid['id'] not in permission_list:
            permission_list.append(pid['id'])
    # 再添加传入的新的权限
    # print(permission_list)
    for permission in permission_list:
        sql = "INSERT INTO role_rel_menu (role_id, menu_id) VALUES ({}, {})".format(role_id, permission)
        base_service.insert(sql)

    return success_response(data="权限设置成功！", path=request.path)