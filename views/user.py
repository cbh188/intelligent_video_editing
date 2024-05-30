from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.sql.functions import user
from werkzeug.security import generate_password_hash

from services import user_service, base_service,org_service
from status import user_status
from utils.response_utils import success_response,error_response
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
    query_total = f"""
                      SELECT count(user_id) AS total FROM user
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
    if len(org_ids) == 1:
        org_ids = f'({org_ids[0]})'
    else:
        org_ids = tuple(org_ids)
    query += " WHERE org_id IN {}".format(org_ids)
    query_total += " WHERE org_id IN {}".format(org_ids)

    if conditions:
        query += " AND " + " AND ".join(conditions)
        query_total += " AND " + " AND ".join(conditions)

    query_with_params = query % tuple(params)
    query_with_params = query_with_params + " ORDER BY user_id"
    query_total_with_params = query_total % tuple(params)
    # print(query_with_params)
    users = base_service.query_page(query_with_params, page_num, page_size)
    for user in users:
        user["gmt_create"] = user["gmt_create"].strftime("%Y-%m-%d %H:%M:%S")
    total = base_service.get_total(query_total_with_params)
    paginated_result = {
        "list": users,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": total
    }
    print(paginated_result)
    return jsonify(success_response(data=paginated_result, path=request.path))

@user_bp.route("/getAllOrgs", methods=["GET"])
@jwt_required()
def get_all_orgs():
    result = org_service.query_all()
    return jsonify(success_response(data=result, path=request.path))

# 新增（编辑）账号
@user_bp.route("", methods=["POST"])
@jwt_required()
def save():
    id = request.json.get("user_id")
    org_id = request.json.get("org_id")
    account = request.json.get("account")
    name = request.json.get("name")
    sex = request.json.get("sex")
    phone = request.json.get("phone")
    email = request.json.get("email")
    repeat_user = user_service.find_user(account)
    if org_id is None:
        return error_response(400, 40001, "组织不能为空", "组织不能为空")
    if id is None:
        # 判断账号是否重复
        if repeat_user is not None:
            return error_response(400, 40001, "账号重复", "账号重复")

        gmt_create = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = user_status.userStatus.OK.get_code()
        avatar = "/avatar/R-C.jpg"
        role_id = "3"

        # 构建 SQL 语句和参数
        sql = "INSERT INTO user (org_id, account, name, gmt_create, status, avatar, role_id"
        values = "VALUES (%s, %s, %s, %s, %s, %s, %s"
        params = [org_id, account, name, gmt_create, status, avatar, role_id]

        # 添加邮箱字段和参数
        if email is not None:
            sql += ", email"
            values += ", %s"
            params.append(email)

        # 添加手机号字段和参数
        if phone is not None:
            sql += ", phone"
            values += ", %s"
            params.append(phone)

        # 添加性别字段和参数
        if sex is not None:
            sql += ", sex"
            values += ", %s"
            params.append(sex)


        # 添加密码和盐
        pwd = "123456"
        pwd_hash = generate_password_hash(pwd, method='MD5')
        pwd_parts = pwd_hash.split("$")
        password = pwd_parts[2]
        salt = pwd_parts[1]
        sql += ", password, salt)"
        values += ", %s, %s)"
        params.extend([password, salt])

        # 完善 SQL 语句
        sql += " " + values
        # print(sql)
        # print(params)
        # print(tuple(params))
        if base_service.insert(sql, params) > 0:
            return success_response(data=pwd, path=request.path)
    else:
        if repeat_user is not None and repeat_user['user_id'] != id:
            return error_response(400, 40001, "账号重复", "账号重复")
        gmt_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "UPDATE user SET org_id = %s, account = %s, name = %s, phone = %s,gmt_modified = %s "
        params = [org_id, account, name, phone, gmt_modified]
        # 添加邮箱字段和参数
        if email is not None:
            sql += ", email = %s"
            params.append(email)

        # 添加性别字段和参数
        if sex is not None:
            sql += ", sex = %s"
            params.append(sex)

        sql += " WHERE user_id = %s"
        params.append(id)
        if base_service.update(sql, params) >= 0:
            return success_response(data=None, path=request.path)

@user_bp.route("", methods=["DELETE"])
@jwt_required()
def remove():
    user_ids = request.args.get("userId")
    # print(user_ids)
    if user_ids is None:
        return error_response(400, 40001, "用户不能为空", "用户不能为空")
    user_ids = [int(user_id) for user_id in user_ids.split(',') if user_id.strip()]
    for user_id in user_ids:
        if int(user_id) < 3:
            return error_response(400, 40001, "不能删除系统管理员", "不能删除系统管理员")
    # print(tuple(user_ids))
    if len(user_ids) == 1:
        sql = "UPDATE user SET status = 3 WHERE user_id = {}".format(user_ids[0])
    else:
        sql = "UPDATE user SET status = 3 WHERE user_id IN {}".format(tuple(user_ids))
    # print(sql)
    base_service.delete(sql)
    return success_response(data=None, path=request.path)

@user_bp.route("/resetPassword", methods=["POST"])
@jwt_required()
def reset_pwd():
    user_id = request.args.get("userId")
    pwd = "123456"
    pwd_hash = generate_password_hash(pwd, method='MD5')
    pwd_parts = pwd_hash.split("$")
    password = pwd_parts[2]
    salt = pwd_parts[1]
    sql = "UPDATE user SET password = %s, salt = %s WHERE user_id = %s"
    params = [password, salt, user_id]
    if base_service.update(sql, tuple(params)) > 0:
        return success_response(data=pwd, path=request.path)

@user_bp.route("/setRole", methods=["POST"])
@jwt_required()
def set_role():
    role_id = request.args.get("roleId")
    user_id = request.args.get("userId")
    sql = "UPDATE user SET role_id = %s WHERE user_id = %s"
    params = [role_id, user_id]
    if base_service.update(sql, tuple(params)) > 0:
        return success_response(data=None, path=request.path)