from flask import Flask, Blueprint, request, jsonify
from services.check_login import is_null,exist_user,pwd_check
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies
from utils.response_utils import handle_errors,success_response,error_response,expire
from utils.log import log_message
from utils.CryptUtil import decrypt
from services import account_service, user_service, menu_service
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
            if user is None:
                return error_response(400, 40001, "用户名或密码错误", "用户名或密码错误")
            if user['status'] == userStatus.FREEZED.value:
                return error_response(400, 40002, "用户被冻结", "用户被冻结")
            elif user['status'] == userStatus.DELETED.value:
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

@account_bp.route('register', methods=['GET', 'POST'])
def register():
    return None

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

