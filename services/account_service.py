
from flask import jsonify
from utils.database import db
def get_my_info(username):
    sql = "SELECT u.*,o.name AS org FROM user u LEFT JOIN organization o ON u.org_id = o.id WHERE u.account = %s AND u.is_deleted = 0"
    db.execute(sql, (username,))
    result = db.cursor.fetchall()
    return result[0]

def get_my_roles(role_id):
    role_id_list = role_id.split(',')
    result = []
    for id in role_id_list:
        sql = "SELECT name FROM role WHERE role_id = %s"
        db.execute(sql, (id,))
        name = db.cursor.fetchone()['name']
        result.append(name)
    return result