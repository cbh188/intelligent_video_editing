from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services import base_service, student_service, user_service, org_service
from utils.date_util import parse_time
from utils.response_utils import success_response, error_response

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
    query_total = f"""
                    SELECT count(student_id) AS total FROM student
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
    # print(query_total_with_params)
    students = base_service.query_page(query_with_params, page_num, page_size)
    for student in students:
        student["create_time"] = student["create_time"].strftime("%Y-%m-%d %H:%M:%S")
        # stu_id = student["student_id"]
        # student["image"] = student_service.read_image(stu_id)
        # student["image"] = str(student["image"], encoding="gb18030")
    total = base_service.get_total(query_total_with_params)
    result = {
        "list": students,
        "pageNum": page_num,
        "pageSize": page_size,
        "total": total
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

@student_bp.route('', methods=['POST'])
@jwt_required()
def save():
    id = request.json.get('student_id')
    org_id = request.json.get('org_id')
    name = request.json.get('name')
    student_no = request.json.get('student_no')
    gender = request.json.get('gender')
    card_id = request.json.get('card_id')
    file_name = request.json.get('fileName')
    # print(file_name)
    repeat_stu = student_service.find_repeat_stu_no(student_no, org_id)
    if org_id is None:
        return error_response(400, 40001, "组织不能为空", "组织不能为空")
    if id is None:
        if repeat_stu:
            return error_response(400, 40001, "在该班级学号重复", "在该班级学号重复")
        if file_name is None:
            return error_response(400, 40001, "图片不能为空", "图片不能为空")

        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        is_deleted = 0
        img_url = "/stu_image/" + file_name
        sql = ("INSERT INTO student (student_no, name, card_id, gender, org_id, image_url, create_time, is_deleted)"
               "VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)")
        params = (student_no, name, card_id, gender, org_id, img_url, create_time, is_deleted)
        if base_service.insert(sql, params) > 0 :
            return success_response(data=student_no, path=request.path)
    else:
        if repeat_stu is not None and repeat_stu['student_id'] != id:
            return error_response(400, 40001, "在该班级已有该学生", "在该班级已有该学生")
        modified_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = "UPDATE student SET student_no = %s, name = %s, card_id = %s, gender = %s, org_id = %s, modified_time = %s"
        params = [student_no, name, card_id, gender, org_id, modified_time]
        if file_name is not None:
            sql += ", image_url = %s"
            params.append("/stu_image/" + file_name)
        sql += " WHERE student_id = %s"
        params.append(id)
        if base_service.update(sql, params) >= 0:
            return success_response(data=None, path=request.path)

@student_bp.route("", methods=["DELETE"])
@jwt_required()
def remove():
    student_ids = request.args.get('studentId')
    # print(student_ids)
    if student_ids is None:
        return error_response(400, 40001, "学生id不能为空", "学生id不能为空")
    student_ids = [int(student_id) for student_id in student_ids.split(',') if student_id.strip()]
    if len(student_ids) == 1:
        sql = "UPDATE student SET is_deleted = 1 WHERE student_id = {}".format(student_ids[0])
    else:
        sql = "UPDATE student SET is_deleted = 1 WHERE student_id IN {}".format(tuple(student_ids))
    # print(sql)
    base_service.delete(sql)
    return success_response(data=None, path=request.path)
@student_bp.route('/upload', methods=['POST'])
def upload():
    if request.files['file'] is not None:
        file = request.files['file']
        # print(file.filename)
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        file.save("C:/work/WebstormProjects/intelligent_video_editing-web/public/stu_image/"+file.filename)
        return success_response(data=None, path=request.path)

@student_bp.route('/getCommentByParent', methods=['GET'])
@jwt_required()
def get_comment():
    parent_account = request.args.get('parentAccount')
    sql = "SELECT c.* FROM comment c LEFT JOIN student s ON c.student_id = s.student_id WHERE s.parent_account = '%s' AND date = '%s'"
    params = [parent_account, datetime.now().strftime('%Y-%m-%d')]
    # print(sql % tuple(params))
    result = base_service.query_all(sql % tuple(params))
    # print(result)
    output = ""
    if len(result) > 0:
        for item in result:
            student_name = student_service.find_student(item['student_id'])['name']
            item['student_name'] = student_name
            comment = item['comment']
            output += student_name + ": " + comment + "\n"
        # comment = result[0]['comment']
    else:
        output = None
    # print(result)
    # print(output)
    return success_response(data=result, path=request.path)

@student_bp.route('/getCommentByStudent', methods=['GET'])
@jwt_required()
def get_comment_by_student():
    student_id = request.args.get('studentId')
    sql = "SELECT * FROM comment WHERE student_id = '%s' AND date = '%s'"
    params = [student_id, datetime.now().strftime('%Y-%m-%d')]
    result = base_service.query_all(sql % tuple(params))
    # print(result)
    if len(result) > 0:
        comment = result[0]['comment']
    else:
        comment = None
    return success_response(data=comment, path=request.path)

@student_bp.route('/saveComment', methods=['POST'])
@jwt_required()
def save_comment():
    student_id = request.json.get('studentId')
    comment = request.json.get('comment')
    date = datetime.now().strftime('%Y-%m-%d')
    if comment is None or comment == "":
        return success_response(data=None, path=request.path)
    else:
        query = "SELECT * FROM comment WHERE student_id = '{}' AND date = '{}'".format(student_id, date)
        if len(base_service.query_all(query)) > 0:
            sql = "UPDATE comment SET comment = '{}' WHERE student_id = '{}' AND date = '{}'".format(comment, student_id, date)
            # print(sql)
            if base_service.update(sql) > 0:
                return success_response(data="更新评价成功！", path=request.path)
        else:
            sql = "INSERT INTO comment (student_id, comment, date) VALUES ('{}', '{}', '{}')".format(student_id, comment, date)
            # print(sql)
            if base_service.insert(sql) > 0:
                return success_response(data="新增评价成功！", path=request.path)

@student_bp.route('/getRecipe', methods=['GET'])
@jwt_required()
def get_recipe():
    org_id = request.args.get('orgId')
    date = datetime.now().strftime('%Y-%m-%d')
    sql = "SELECT * FROM recipe WHERE org_id = '%s' AND date = '%s'"
    params = [org_id, date]
    result = base_service.query_all(sql % tuple(params))
    if len(result) > 0:
        recipe = result[0]['menu']
    else:
        recipe = None
    print("食谱为：", recipe)
    # list = recipe.split(";")
    # print(list)
    return success_response(data=recipe, path=request.path)

@student_bp.route('/saveRecipe', methods=['POST'])
@jwt_required()
def save_recipe():
    org_id = request.json.get('orgId')
    recipe = request.json.get('recipe')
    date = datetime.now().strftime('%Y-%m-%d')
    if recipe is None or recipe == "":
        return success_response(data=None, path=request.path)
    else:
        query = "SELECT * FROM recipe WHERE org_id = '{}' AND date = '{}'".format(org_id, date)
        if len(base_service.query_all(query)) > 0:
            sql = "UPDATE recipe SET menu = '{}' WHERE org_id = '{}' AND date = '{}'".format(recipe, org_id, date)
            # print(sql)
            if base_service.update(sql) > 0:
                return success_response(data="更新食谱成功！", path=request.path)
        else:
            sql = "INSERT INTO recipe (org_id, menu, date) VALUES ('{}', '{}', '{}')".format(org_id, recipe, date)
            # print(sql)
            if base_service.insert(sql) > 0:
                return success_response(data="新增食谱成功！", path=request.path)