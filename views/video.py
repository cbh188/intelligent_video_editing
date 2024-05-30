import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, user_service, org_service, student_service, video_service
from utils import video_util
from utils.date_util import parse_time
from utils.response_utils import success_response, handle_errors, error_response

video_bp = Blueprint('video', __name__, url_prefix='/video')

@video_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    video_no = request.args.get('video_no')
    video_title = request.args.get('video_title')
    upload_user = request.args.get('upload_user')
    org_id = request.args.get('org_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))

    query = f"""
                SELECT video_id,video_no,video_title,video_url,upload_user,org_id,upload_time FROM video 
            """
    query_total = f"""
                        SELECT count(video_id) AS total FROM video
                      """
    conditions = []
    params = []

    condition, param = base_service.build_fuzzy_search_conditions("video_no", video_no)
    if condition:
        conditions.append(condition)
        params.append(param)

    condition, param = base_service.build_fuzzy_search_conditions("video_title", video_title)
    if condition:
        conditions.append(condition)
        params.append(param)

    condition, param = base_service.build_fuzzy_search_conditions("upload_user", upload_user)
    if condition:
        conditions.append(condition)
        params.append(param)

    if org_id is not None:
        conditions.append("org_id = %s")
        params.append(org_id)

    if start_time:
        start_time = parse_time(start_time)
        conditions.append("upload_time >= '%s'")
        params.append(start_time)

    if end_time:
        end_time = parse_time(end_time)
        conditions.append("upload_time <= '%s'")
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
    query += " WHERE org_id IN {} AND is_deleted = 0".format(org_ids)
    query_total += " WHERE org_id IN {} AND is_deleted = 0".format(org_ids)

    if conditions:
        query += " AND " + " AND ".join(conditions)
        query_total += " AND " + " AND ".join(conditions)

    query_with_params = query % tuple(params)
    query_total_with_params = query_total % tuple(params)
    # print(query_with_params)
    videos = base_service.query_page(query_with_params, page_num, page_size)
    for video in videos:
        video["upload_time"] = video["upload_time"].strftime("%Y-%m-%d %H:%M:%S")
    total = base_service.get_total(query_total_with_params)
    result = {
        "list": videos,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": total
    }
    # print(result)
    return jsonify(success_response(data=result, path=request.path))

@video_bp.route('', methods=['POST'])
@jwt_required()
def save():
    org_id = request.json.get("org_id")
    video_no = request.json.get("video_no")
    video_title = request.json.get("video_title")
    file_name = request.json.get("fileName")

    repeat_video = video_service.find_repeat_video(video_no, org_id)
    if org_id is None:
        return error_response(400, 40001, "组织不能为空", "组织不能为空")
    if repeat_video:
        return error_response(400, 40001, "在该组织视频编号重复", "在该组织视频编号重复")
    if file_name is None:
        return error_response(400, 40001, "视频不能为空", "视频不能为空")

    upload_time = request.json.get("upload_time")
    upload_user = request.json.get("upload_user")
    video_url = "/video/" + file_name
    is_deleted = 0
    sql = "INSERT INTO video(video_no,video_title,video_url,upload_user,org_id,upload_time,is_deleted) VALUES (%s,%s,%s,%s,%s,%s,%s)"
    params = (video_no, video_title, video_url, upload_user, org_id, upload_time, is_deleted)
    if base_service.insert(sql, params) > 0:
        return success_response(data=video_no, path=request.path)

@video_bp.route('', methods=['DELETE'])
@jwt_required()
def remove():
    video_ids = request.args.get('videoId')
    print(video_ids)
    if video_ids is None:
        return error_response(400, 40001, "视频不能为空", "视频不能为空")
    video_ids = [int(video_id) for video_id in video_ids.split(",") if video_id.strip()]
    if len(video_ids)  == 1:
        sql = "UPDATE video SET is_deleted = 1 WHERE video_id = {}".format(video_ids[0])
    else:
        sql = "UPDATE video SET is_deleted = 1 WHERE video_id IN {}".format(tuple(video_ids))
    base_service.delete(sql)
    return success_response(data=None, path=request.path)

@video_bp.route('/edit', methods=['POST'])
@jwt_required()
def edit():
    student_id = request.args.get('studentId')
    image_url = student_service.get_image_url(student_id)
    video_id = request.args.get('videoId')
    video_url = request.args.get('videoUrl')
    current_account = get_jwt_identity()
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print("student_id", student_id)
    print("image_url", image_url)
    print("video_id", video_id)
    print("video_url", video_url)
    #  直接传视频url
    output_path = video_service.video_editing(video_id, student_id, video_url, image_url, threshold=0.6)
    output_url = output_path.replace("C:/work/WebstormProjects/intelligent_video_editing-web/public", "")
    print("output_url", output_url)
    video_service.save_edited_video(output_url,current_account, create_time, student_id)
    video_service.save_edit_log(video_id, student_id, current_account, create_time)
    return jsonify(success_response(data=output_url, path=request.path))

@video_bp.route('/mutiEdit', methods=['POST'])
@jwt_required()
def muti_edit():
    student_id = request.json.get('studentId')
    image_url = student_service.get_image_url(student_id)
    video_ids = request.json.get('videoIds')
    video_urls = request.json.get('videoUrls')
    current_account = get_jwt_identity()

    print("student_id", student_id)
    print("image_url", image_url)
    print("video_ids", video_ids)
    print("video_urls", video_urls)
    output_paths = []
    for video_id, video_url in zip(video_ids, video_urls):
        output_path = video_service.video_editing(video_id, student_id, video_url, image_url, threshold=0.6)
        if output_path != "视频中没有匹配的人脸":
            output_paths.append(output_path)
    print(output_paths)
    # 视频拼接
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    output_name = current_account + "_" + current_time + ".mp4"
    video_util.concat_video(output_paths, output_name)
    output_url = "/output/" + output_name
    video_service.save_edited_video(output_url, current_account, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), student_id)
    for video_id in video_ids:
        video_service.save_edit_log(video_id, student_id, current_account, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return success_response(data=output_url, path=request.path)

@video_bp.route('/upload', methods=['POST'])
def upload():
    if request.files['file'] is not None:
        file = request.files['file']
        # print(file.filename)
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        file.save("C:/work/WebstormProjects/intelligent_video_editing-web/public/video/"+file.filename)
        return success_response(data=None, path=request.path)

@video_bp.route('/edited/list', methods=['GET'])
@jwt_required()
def video_edited_list():
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    student_name = request.args.get('student_name')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))
    create_by = get_jwt_identity()

    query = f"""
                SELECT v.*, s.name AS student_name FROM video_edited v LEFT JOIN student s ON v.student_id = s.student_id  
            """
    query_total = f"""
                        SELECT count(id) AS total FROM video_edited v LEFT JOIN student s ON v.student_id = s.student_id
                    """
    params = []

    if student_name:
        query += " WHERE ( v.create_by = '%s' AND s.name LIKE '%s')"
        query_total += " WHERE ( v.create_by = '%s'  AND s.name LIKE '%s')"
        params.append(create_by)
        params.append("%" + student_name + "%")
    else:
        query += " WHERE (v.create_by = '%s' OR v.student_id IS NULL)"
        query_total += " WHERE (v.create_by = '%s' OR v.student_id IS NULL)"
        params.append(create_by)

    if start_time:
        start_time = parse_time(start_time)
        query += " AND v.create_time >= '%s'"
        query_total += " AND v.create_time >= '%s'"
        params.append(start_time)

    if end_time:
        end_time = parse_time(end_time)
        query += " AND v.create_time <= '%s'"
        query_total += " AND v.create_time <= '%s'"
        params.append(end_time)

    # print(params)
    query_with_params = query % tuple(params) + " ORDER BY v.create_time DESC"
    query_total_with_params = query_total % tuple(params)
    print(query_with_params)
    # print(query_total_with_params)
    video_edited_list = base_service.query_page(query_with_params, page_num, page_size)
    for video_edited in video_edited_list:
        video_edited["create_time"] = video_edited["create_time"].strftime("%Y-%m-%d %H:%M:%S")
    total = base_service.get_total(query_total_with_params)
    result = {
        "list": video_edited_list,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": total
    }
    # print(result)
    return jsonify(success_response(data=result, path=request.path))

@video_bp.route('/edited', methods=['DELETE'])
@jwt_required()
def remove_video_edited():
    video_edited_ids = request.args.get('videoId')
    # print(video_edited_ids)
    if video_edited_ids is None:
        return error_response(400, 40001, "视频不能为空", "视频不能为空")
    video_edited_ids = [int(video_edited_id) for video_edited_id in video_edited_ids.split(",") if video_edited_id.strip()]
    if len(video_edited_ids) == 1:
        sql = "DELETE FROM video_edited WHERE id = {}".format(video_edited_ids[0])
    else:
        sql = "DELETE FROM video_edited WHERE id IN {}".format(tuple(video_edited_ids))
    base_service.delete(sql)
    return success_response(data=None, path=request.path)

@video_bp.route('/concat', methods=['POST'])
@jwt_required()
def concat():
    video_ids = request.json.get('ids')
    url_list = request.json.get('urls')
    current_user = get_jwt_identity()
    # print(video_ids)
    # print(url_list)
    video_list = []
    for url in url_list:
        video_url = "C:/work/WebstormProjects/intelligent_video_editing-web/public" + url
        video_list.append(video_url)
    # print(video_list)
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    # print(current_time)
    output_name = current_user + "_" + current_time + ".mp4"
    # print(output_name)
    video_util.concat_video(video_list, output_name)
    output_url = "/output/" + output_name
    video_service.save_edited_video(output_url, current_user, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return success_response(data=None, path=request.path)

@video_bp.route('/music/upload', methods=['POST'])
def upload_music():
    if request.files['file'] is not None:
        file = request.files['file']
        # print(file.filename)
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        file.save("C:/work/WebstormProjects/intelligent_video_editing-web/public/music/"+file.filename)
        return success_response(data=None, path=request.path)

@video_bp.route('/addBgm', methods=['POST'])
@jwt_required()
def add_bgm():
    video_url = request.json.get('url')
    create_by = get_jwt_identity()
    bgm_name = request.json.get('fileName')
    # print(video_url, create_by, bgm_name)
    base_url = "C:/work/WebstormProjects/intelligent_video_editing-web/public"
    video = base_url + video_url
    bgm_url = base_url + "/music/" + bgm_name
    output_dir = base_url + "/output"
    result = video_util.video_add_audio(video, bgm_url, output_dir, create_by)
    # print(result)
    url = result.replace(base_url, "")
    # print(url)
    video_service.save_edited_video(url, create_by, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return success_response(data=None, path=request.path)