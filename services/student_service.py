from services import org_service
from utils.database import db
from PIL import Image
from io import BytesIO
import base64

# 根据学生id读取照片
def read_image(student_id):
    sql = "SELECT image FROM student WHERE student_id = %s"
    db.execute(sql, (student_id,))
    image_data = db.cursor.fetchone()['image']
    image = Image.open(BytesIO(image_data))
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    return image_base64

def list_all(my_org_id):
    sql = "SELECT student_id,student_no,name,gender,card_id,org_id,image_url,create_time FROM student"
    org_list = org_service.query_all_sub(my_org_id)
    org_ids = []
    for org in org_list:
        org_ids.append(org['id'])
    if len(org_ids) == 1:
        sql += f" WHERE org_id IN ({org_ids[0]})"
    else:
        sql += f" WHERE org_id IN {tuple(org_ids)}"
    # sql += " WHERE org_id IN {}".format(tuple(org_ids))
    # print(sql)
    db.execute(sql)
    result = db.cursor.fetchall()
    return result

def get_image_url(student_id):
    sql = "SELECT image_url FROM student WHERE student_id = %s AND is_deleted = 0"
    db.execute(sql, (student_id,))
    image_url = db.cursor.fetchone()['image_url']
    return image_url