from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, student_service, user_service, org_service
from utils.date_util import parse_time
from utils.response_utils import success_response

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/list', methods=['GET'])
@jwt_required()
def list():
    stu_no = request.args.get('student_no')
    name = request.args.get('name')
    gender = request.args.get('gender')
    card_id = request.args.get('card_id')
    org_id = request.args.get('org_id')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    page_num = int(request.args.get('pageNum', 1))
    page_size = int(request.args.get('pageSize', 10))

    query = f"""
                SELECT student_id,student_no,name,gender,card_id,org_id,image_url,create_time FROM student
            """
    conditions = []
    params = []

    condition, param = base_service.build_fuzzy_search_conditions("name", name)
    if condition:
        conditions.append(condition)
        params.append(param)

    condition, param = base_service.build_fuzzy_search_conditions("student_no", stu_no)
    if condition:
        conditions.append(condition)
        params.append(param)

    if gender is not None:
        conditions.append("gender = %s")
        params.append(gender)

    if card_id is not None:
        conditions.append("card_id = %s")
        params.append(card_id)

    if org_id is not None:
        conditions.append("org_id = %s")
        params.append(org_id)

    if start_time:
        start_time = parse_time(start_time)
        conditions.append("create_time >= '%s'")
        params.append(start_time)

    if end_time:
        end_time = parse_time(end_time)
        conditions.append("create_time <= '%s'")
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

    students = base_service.query_page(query_with_params, page_num, page_size)
    for student in students:
        student["create_time"] = student["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        # stu_id = student["student_id"]
        # student["image"] = student_service.read_image(stu_id)
        # student["image"] = str(student["image"], encoding="gb18030")
    result = {
        "list": students,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": len(students)
    }
    # print(result)
    return jsonify(success_response(data=result, path=request.path))

@student_bp.route('/listAll', methods=['GET'])
@jwt_required()
def list_all():
    current_user = get_jwt_identity()
    my_org_id = user_service.find_user(current_user)['org_id']
    result = student_service.list_all(my_org_id)
    # print("all students", result)
    return jsonify(success_response(data=result, path=request.path))