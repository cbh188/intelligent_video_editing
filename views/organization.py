from datetime import datetime

from flask import Blueprint,jsonify,request
from services import org_service, user_service, base_service
from utils.response_utils import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity
org_bp = Blueprint('org', __name__, url_prefix='/org')

@org_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    current_user = get_jwt_identity()
    my_org_id = user_service.find_user(current_user)['org_id']
    # print("my org id:",my_org_id)
    result = org_service.query_all_node(my_org_id)
    # print(result)
    return jsonify(success_response(data=result,path=request.url))

@org_bp.route('', methods=['POST'])
@jwt_required()
def save():
    id = request.json.get('id')
    pid = request.json.get('pid')
    name = request.json.get('name')
    org_code = request.json.get('org_code')
    num = request.json.get('num')
    repeat_org = org_service.find_org_by_code(org_code)
    if pid is None:
        return error_response(400, 40001, "父组织不能为空", "父组织不能为空")
    if id is None:
        if repeat_org is not None:
            return error_response(400, 40001, "组织编码重复", "组织编码重复")

        create_ime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        is_deleted = 0
        pids = org_service.get_pids(pid) + "[{}],".format(pid)
        sql = ("INSERT INTO organization (org_code, name, num, pid, pids, create_time, is_deleted) "
               "VALUES (%s, %s, %s, %s, %s, %s, %s)")
        print(sql)
        params = (org_code, name, num, pid, pids, create_ime, is_deleted)
        if base_service.insert(sql, params) > 0 :
            return success_response(data=org_code, path=request.url)
    else:
        if repeat_org is not None and repeat_org['id'] != id:
            return error_response(400, 40001, "组织编码重复", "组织编码重复")
        modified_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = ("UPDATE organization SET org_code=%s, name=%s, num=%s, pid=%s, modified_time=%s WHERE id=%s")
        params = [org_code, name, num, pid, modified_time, id]
        if base_service.update(sql, params) >= 0:
            return success_response(data=None, path=request.url)

@org_bp.route('', methods=['DELETE'])
@jwt_required()
def remove():
    ids = request.args.getlist('id')[0]
    # print(ids)
    if ids is None:
        return error_response(400, 40001, "组织不能为空", "组织不能为空")
    ids = [int(id) for id in ids.split(',') if id.strip()]
    for id in ids:
        if int(id) < 3:
            return error_response(400, 40001, "不能删除根组织", "不能删除根组织")
    if len(ids) == 1:
        sql = "UPDATE organization SET is_deleted = 1 WHERE id = {}".format(ids[0])
    else:
        sql = "UPDATE organization SET is_deleted = 1  WHERE id IN {}".format(tuple(ids))
    base_service.delete(sql)
    return success_response(data=None, path=request.url)

@org_bp.route('/getClassStatsList', methods=['GET'])
@jwt_required()
def get_class_stats_list():
    current_user_account = get_jwt_identity()
    current_user = user_service.find_user(current_user_account)
    my_org_id = current_user['org_id']
    this_month = datetime.now().strftime("%Y-%m-01")
    result = []

    # 获取班级名和班级管理员
    sql = "SELECT u.account,u.org_id,o.name FROM user u LEFT JOIN organization o ON u.org_id = o.id WHERE o.pid = '{}' AND u.role_id = '4'".format(my_org_id)
    res = base_service.query_all(sql)
    for r in res:
        item = {}
        item['org_id'] = r['org_id']
        item['org_name'] = r['name']
        item['account'] = r['account']
        result.append(item)

    for item in result:
        org_id = item['org_id']
        # 获取每个班级总共上传的视频
        sql = "SELECT org_id,COUNT(*) AS total_upload FROM video WHERE org_id = '{}' GROUP BY org_id".format(org_id)
        item['total_upload'] = base_service.query_all(sql)[0]['total_upload']
        # 获取每个班级本月上传的视频
        sql = "SELECT org_id,COUNT(*) AS month_upload FROM video WHERE org_id = '{}' AND upload_time >= '{}' GROUP BY org_id".format(org_id, this_month)
        item['month_upload'] = base_service.query_all(sql)[0]['month_upload']
        # 获取每个班级总共剪辑的视频
        sql = "SELECT v.org_id,COUNT(*) AS total_edit FROM edit_log e LEFT JOIN video v ON e.video_id = v.video_id WHERE org_id = '{}' GROUP BY v.org_id".format(org_id)
        item['total_edit'] = base_service.query_all(sql)[0]['total_edit']
        # 获取每个班级本月剪辑的视频
        sql = "SELECT v.org_id,COUNT(*) AS month_edit FROM edit_log e LEFT JOIN video v ON e.video_id = v.video_id WHERE org_id = '{}' AND e.create_time >= '{}' GROUP BY v.org_id".format(org_id, this_month)
        item['month_edit'] = base_service.query_all(sql)[0]['month_edit']
        item['score'] = item['month_upload'] * 2 + item['month_edit'] * 0.8

    # 根据score排序
    sorted_data = sorted(result, key=lambda x: x['score'], reverse=True)

    # 将排名加入字典中
    for rank, item in enumerate(sorted_data, start=1):
        item['rank'] = rank


    print(sorted_data)

    return success_response(data=sorted_data, path=request.url)

