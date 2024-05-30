from werkzeug.security import generate_password_hash, check_password_hash
from flask import jsonify
from utils.database import db
def get_my_info(username):
    sql = "SELECT u.*,o.name AS org FROM user u LEFT JOIN organization o ON u.org_id = o.id WHERE u.account = %s"
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

def update_pwd(username, new_pwd):
    try:
        pwd = generate_password_hash(new_pwd, method='MD5')
        pwd_parts = pwd.split('$')
        password = pwd_parts[2]
        salt = pwd_parts[1]
        sql = "UPDATE user SET password = %s, salt = %s WHERE account = %s"
        db.execute(sql, (password, salt, username))
        return True
    except Exception as e:
        print(e)
        return False