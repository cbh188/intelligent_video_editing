import os

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, user_service, org_service, student_service, video_service
from utils.date_util import parse_time
from utils.response_utils import success_response, handle_errors

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
        query += " WHERE is_deleted = 0 AND org_id IN ({})".format(org_ids[0])
    else:
        query += " WHERE is_deleted = 0 AND org_id IN {}".format(tuple(org_ids))

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query_with_params = query % tuple(params)
    # print(query_with_params)
    videos = base_service.query_page(query_with_params, page_num, page_size)
    for video in videos:
        video["upload_time"] = video["upload_time"].strftime("%Y-%m-%d %H:%M:%S")

    result = {
        "list": videos,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": len(videos)
    }
    # print(result)
    return jsonify(success_response(data=result, path=request.path))

@video_bp.route('/edit', methods=['POST'])
@jwt_required()
def edit():
    student_id = request.args.get('studentId')
    image_url = student_service.get_image_url(student_id)
    video_id = request.args.get('videoId')
    video_url = request.args.get('videoUrl')

    print("student_id", student_id)
    print("image_url", image_url)
    print("video_id", video_id)
    print("video_url", video_url)
    #  直接传视频url
    output_path = video_service.video_editing(video_id, student_id, video_url, image_url, threshold=0.6)
    output_url = output_path.replace("C:/work/WebstormProjects/intelligent_video_editing-web/public", "")
    print("output_url", output_url)
    return jsonify(success_response(data=output_url, path=request.path))