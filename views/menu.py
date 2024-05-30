from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from dao import menu_repository
from services import base_service, menu_service, user_service
from utils.response_utils import success_response, error_response

menu_bp = Blueprint('menu', __name__, url_prefix='/menu')


@menu_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    menu_list = menu_service.get_menus()
    print(menu_list)
    return jsonify(success_response(data=menu_list, path=request.path))


@menu_bp.route('', methods=['POST'])
@jwt_required()
def save():
    id = request.json.get('id')
    code = request.json.get('code')
    component = request.json.get('component')
    icon = request.json.get('icon')
    is_menu = request.json.get('ismenu')
    name = request.json.get('name')
    num = request.json.get('num')
    hidden = request.json.get('hidden')
    pcode = request.json.get('pcode')
    url = request.json.get('url')
    current_user = get_jwt_identity()
    user_id = user_service.find_user(current_user)['user_id']
    repeat_menu = menu_repository.find_menu_by_code(code)

    if id is None:
        if repeat_menu is not None:
            return error_response(400, 4001, "菜单编码重复", "菜单编码重复")
        create_by = user_id
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if pcode is None or pcode == '':
            pcode = 0
            pcodes = '[0],'
        else:
            pcodes = menu_repository.find_menu_by_code(pcode)['pcodes'] + '[{}],'.format(pcode)
        # print(pcodes)
        levels = pcodes.count(',')
        if hidden:
            hidden = True
        else:
            hidden = False
        print(hidden)
        sql = (
            "INSERT INTO menu (create_by, create_time, code, component, hidden, icon, ismenu, levels, name, num, pcode, pcodes, url)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        params = [create_by, create_time, code, component, hidden, icon, is_menu, levels, name, num, pcode, pcodes, url]
        if base_service.insert(sql, params) > 0:
            return success_response(data=None, path=request.path)
    else:
        if repeat_menu is not None and repeat_menu['id'] != id:
            return error_response(400, 4001, "菜单编码重复", "菜单编码重复")
        modify_by = user_id
        modify_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if pcode is None or pcode == '':
            pcode = 0
            pcodes = '[0],'
        else:
            pcodes = menu_repository.find_menu_by_code(pcode)['pcodes'] + '[{}],'.format(pcode)
        # print(pcodes)
        levels = pcodes.count(',')
        if hidden:
            hidden = True
        else:
            hidden = False
        print(hidden)
        sql = ("UPDATE menu SET modify_by = %s, modify_time = %s, code = %s, component = %s, "
               "hidden = %s, icon = %s, levels = %s, name = %s, num = %s, pcode = %s ,pcodes = %s, url = %s"
               "WHERE id = %s")
        params = [modify_by, modify_time, code, component, hidden, icon, levels, name, num, pcode, pcodes, url, id]
        if base_service.update(sql, params) >= 0:
            return success_response(data=None, path=request.path)


@menu_bp.route('', methods=['DELETE'])
@jwt_required()
def remove():
    menu_ids = request.args.getlist('id[]')
    menu_ids = [int(id) for id in menu_ids]
    # print(menu_ids)
    if len(menu_ids) == 1:
        sql = "DELETE FROM menu WHERE id = {}".format(menu_ids[0])
    else:
        sql = "DELETE FROM menu WHERE id IN {}".format(tuple(menu_ids))
    base_service.delete(sql)
    return success_response(data=None, path=request.path)


# 获取菜单树
@menu_bp.route('/menuTreeListByRoleId', methods=['GET'])
@jwt_required()
def menu_tree_list_by_role_id():
    role_id = request.args.get('roleId')
    menu_ids = menu_service.get_menuIds_by_roleId(role_id)
    # print(menu_ids)
    # role_tree_list = []
    if menu_ids is None or len(menu_ids) == 0:
        role_tree_list = menu_service.menu_tree_list()
    else:
        role_tree_list = menu_service.menu_tree_list(tuple(menu_ids))

    list = menu_service.generate_menu_tree_for_role(role_tree_list)
    # print(list)
    # print("role_tree_list:", role_tree_list)
    # 将 role_tree_list 转换为字典，以便能够通过 id 快速查找 ZTreeNode 对象
    tree_map = {node['id']: node for node in role_tree_list}

    # 根据父节点分组 element-ui中tree控件中如果选中父节点会默认选中所有子节点，所以这里将所有非叶子节点去掉
    grouped_nodes = {}
    for node in role_tree_list:
        grouped_nodes.setdefault(node['pId'], []).append(node)
    # print(tree_map)
    # print(grouped_nodes)
    # 移除所有非叶子节点
    for p_id, nodes in grouped_nodes.items():
        # print(p_id, nodes)
        if len(nodes) > 1:
            # 如果当前节点有多个子节点，则移除父节点
            if p_id in tree_map:
                role_tree_list.remove(tree_map[p_id])

    # 打印移除非叶子节点后的列表
    # print("after role_tree_list:", role_tree_list)

    checked_ids = []
    for z_tree_node in role_tree_list:
        if z_tree_node['checked'] == 'true':
            # print(z_tree_node)
            checked_ids.append(z_tree_node['id'])
    # print(checked_ids)
    return success_response(data={"treeData": list, "checkedIds": checked_ids}, path=request.path)
