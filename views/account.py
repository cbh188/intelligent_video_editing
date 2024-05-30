from datetime import datetime, timedelta

from flask import Flask, Blueprint, request, jsonify
from services.check_login import is_null,exist_user,pwd_check
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from utils.response_utils import handle_errors,success_response,error_response,expire
from utils.log import log_message
from utils.CryptUtil import decrypt
from services import account_service, user_service, menu_service, base_service
from status.user_status import userStatus

account_bp = Blueprint('account', __name__, url_prefix='/account')


# 登录接口
@handle_errors
@account_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.json.get('username')
            password = request.json.get('password')
            try:
                password = decrypt(password)
            except Exception as e:
                log_message('密码未加密')
            user = user_service.find_user(username)
            # print("user:", user)
            if user is None:
                return error_response(400, 40001, "用户名或密码错误", "用户名或密码错误")
            if user['status'] == userStatus.FREEZED.get_code():
                return error_response(400, 40002, "用户被冻结", "用户被冻结")
            elif user['status'] == userStatus.DELETED.get_code():
                return error_response(400, 40003, "用户已删除", "用户已删除")
            if user['role_id'] is None:
                return error_response(400, 40004, "该用户未配置权限", "该用户未配置权限")

            if is_null(username, password):
                login_message = "温馨提示：用户名或密码不能为空"
                return error_response(400, 40006, login_message, login_message)
            elif pwd_check(username, password):
                access_token = create_access_token(identity=username)
                print("access_token:", access_token)
                return jsonify(success_response(data={'token': access_token}, path=request.url))
            elif exist_user(username):
                login_message = "温馨提示：密码错误，请输入正确密码，如忘记密码请联系管理员"
                return error_response(400, 40006, login_message, login_message)
            else:
                login_message = "温馨提示：不存在该用户或用户状态失效，请联系管理员"
                return error_response(400, 40006, login_message, login_message)

        except Exception as e:
            log_message(e)
        return error_response(400, 40005, "未知错误,登陆失败", "登陆失败")

@account_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify(success_response(data={'token': access_token}, path=request.url))

@account_bp.route('/updatePwd', methods=['POST'])
@jwt_required()
def update_pwd():
    try:
        old_password = request.args.get('oldPassword')
        password = request.args.get('password')
        re_password = request.args.get('rePassword')
        current_user = get_jwt_identity()
        if old_password == '' or password == '':
            return error_response(400, 40006, "密码不能为空", "密码不能为空")
        if password != re_password:
            return error_response(400, 40006, "前后密码不一致", "前后密码不一致")
        if not pwd_check(current_user,old_password):
            return error_response(400, 40006, "旧密码输入错误", "旧密码输入错误")
        if account_service.update_pwd(current_user, password):
            return jsonify(success_response(data={'message': '密码修改成功'}, path=request.url))
    except Exception as e:
        log_message(e)
    return error_response(400, 40005, "未知错误,修改密码失败", "修改密码失败")

@account_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    print(current_user)
    return jsonify(logged_in_as=current_user), 200

@account_bp.route('/info', methods=['GET'])
@jwt_required()
def info():
    current_user = get_jwt_identity()
    print(current_user)
    myInfo = account_service.get_my_info(current_user)
    # print(myInfo)
    result = {"username": myInfo["account"], "name": myInfo["name"], "roles": myInfo["role_id"]}
    del myInfo['password']
    del myInfo['salt']
    role_id = myInfo['role_id']
    roles = account_service.get_my_roles(role_id)
    myInfo["roles"] = roles
    result["profile"] = myInfo
    # print(myInfo)
    print(result)
    return jsonify(success_response(data=result, path=request.url))

@account_bp.route('/menu/list', methods=['GET'])
@jwt_required()
def menu_list():
    current_user = get_jwt_identity()
    if current_user is not None:
        user = user_service.find_user(current_user)
        if user is None:
            return expire()
        if user['role_id'] is None:
            return error_response(400, 40004, "该用户未配置权限", "该用户未配置权限")
        menu_list = menu_service.get_side_bar_menus(user['role_id'])
        print(menu_list)
        return jsonify(success_response(data=menu_list, path=request.url))
    return error_response(400, 40005, "未知错误,获取菜单失败", "未知错误,获取菜单失败")

@account_bp.route('/button/list', methods=['GET'])
@jwt_required()
def button_list():
    current_user = get_jwt_identity()
    if current_user is not None:
        user = user_service.find_user(current_user)
        if user is None:
            return expire()
        if user['role_id'] is None:
            return error_response(400, 40004, "该用户未配置权限", "该用户未配置权限")
        result = menu_service.get_button_auth(user['role_id'])
        print(result)
        return jsonify(success_response(data=result, path=request.url))
    return error_response(400, 40005, "未知错误,获取按钮权限失败", "未知错误,获取按钮权限失败")

@account_bp.route('/teacherStats', methods=['GET'])
@jwt_required()
def get_stats():
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    my_org_id = current_user['org_id']
    # print(my_org_id)
    result = {}
    # 用户数量
    sql = "SELECT * FROM user WHERE org_id = '{}' AND status = '1'".format(my_org_id)
    user_num = base_service.count(sql)
    result['user_num'] = user_num
    # print(user_num)

    # 视频数量
    sql = "SELECT * FROM video WHERE org_id = '{}' AND is_deleted = '0'".format(my_org_id)
    video_num = base_service.count(sql)
    result['video_num'] = video_num

    # 学生数量
    sql = "SELECT * FROM student WHERE org_id = '{}' AND is_deleted = '0'".format(my_org_id)
    student_num = base_service.count(sql)
    result['student_num'] = student_num

    # 本月发布视频数
    sql = "SELECT * FROM video WHERE org_id = '{}' AND is_deleted = '0' AND upload_time >= '{}'".format(my_org_id, datetime.now().strftime("%Y-%m-01"))
    upload_num = base_service.count(sql)
    result['upload_num'] = upload_num

    # 本月剪辑视频数
    sql = "SELECT e.* FROM edit_log e LEFT JOIN user u ON e.create_by = u.account WHERE u.org_id = '{}' AND e.create_time >= '{}'".format(my_org_id, datetime.now().strftime("%Y-%m-01"))
    edit_num = base_service.count(sql)
    result['edit_num'] = edit_num

    print(result)

    return success_response(data=result, path=request.url)

@account_bp.route('/schoolStats', methods=['GET'])
@jwt_required()
def get_school_stats():
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    my_org_id = current_user['org_id']

    result = {}
    # 获取班级数量
    sql = "SELECT * FROM organization WHERE pid = '{}' AND is_deleted = '0'".format(my_org_id)
    class_num = base_service.count(sql)
    classes = base_service.query_all(sql)
    org_ids = []
    for org in classes:
        org_id = org['id']
        org_ids.append(org_id)
    # print(org_ids)
    result['class_num'] = class_num

    # 获取用户数量
    sql = "SELECT * FROM user WHERE org_id IN {} AND status = '1'".format(tuple(org_ids))
    user_num = base_service.count(sql)
    result['user_num'] = user_num

    # 获取视频数量
    sql = "SELECT * FROM video WHERE org_id IN {} AND is_deleted = '0'".format(tuple(org_ids))
    video_num = base_service.count(sql)
    result['video_num'] = video_num

    # 获取学生数量
    sql = "SELECT * FROM student WHERE org_id IN {} AND is_deleted = '0'".format(tuple(org_ids))
    student_num = base_service.count(sql)
    result['student_num'] = student_num

    return success_response(data=result, path=request.url)

@account_bp.route('/generateSchoolChart', methods=['GET'])
@jwt_required()
def generate_school_graph():
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    my_org_id = current_user['org_id']

    result = {}

    # 获取近七天的日期
    # 获取今天的日期
    today = datetime.now().date()
    # 生成七天前的日期
    seven_days_ago = today - timedelta(days=7)

    # 创建一个日期列表，从七天前到今天
    date_list = [seven_days_ago + timedelta(days=i) for i in range(7)]  # 8 是因为要包括今天

    # 将日期格式化为字符串
    date_strings = [date.strftime("%m-%d") for date in date_list]

    print(date_strings)
    result['date_list'] = date_strings

    # 获取所有班级名称
    sql = "SELECT * FROM organization WHERE pid = '{}' AND is_deleted = '0'".format(my_org_id)
    classes = base_service.query_all(sql)
    class_names = []
    for class_ in classes:
        class_name = class_['name']
        class_names.append(class_name)
    result['class_names'] = class_names

    class_edit_nums_list = []
    # 获取每个班级近七天每天的的视频剪辑数
    for class_ in classes:
        class_edit_nums = {}
        class_name = class_['name']
        class_id = class_['id']
        edit_num_list = []
        for date_string in date_strings:
            sql = "SELECT e.* FROM edit_log e LEFT JOIN video v ON e.video_id = v.video_id WHERE v.org_id = '{}' AND create_time LIKE '%{}%'".format(class_id, date_string)
            edit_num = base_service.count(sql)
            edit_num_list.append(edit_num)
        class_edit_nums[class_name] = edit_num_list
        class_edit_nums_list.append(class_edit_nums)
    print(class_edit_nums_list)
    result['class_edit_nums'] = class_edit_nums_list
    return success_response(data=result, path=request.url)