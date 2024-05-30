from utils.database import db
from services import org_service

def get_user_by_id(user_id):
    """
    根据用户id查询用户
    :param user_id: 用户id
    :return: 用户信息
    """
    sql = "SELECT * FROM user WHERE user_id= %s"
    db.execute(sql, (user_id,))
    result = db.cursor.fetchone()
    return result

def find_user(username):
    """
    根据用户名查找用户
    :param username: 用户名
    :return: 用户信息
    """
    sql = "SELECT * FROM user WHERE account= %s"
    db.execute(sql, (username,))
    result = db.cursor.fetchone()
    # print(result)
    return result

def query_users():
    """
    查询所有用户
    :return: 用户列表
    """
    sql = "SELECT user_id,name,account,org_id,sex,email,gmt_create,phone,status FROM user"
    db.execute(sql)
    result = db.cursor.fetchall()
    return result

def query_users_sub(my_org_id):
    org_list = org_service.query_all_sub(my_org_id)
    org_ids = []
    for org in org_list:
        org_ids.append(org['id'])
    print(org_ids)
    sql = """
        SELECT user_id, name, account, org_id, sex, email, gmt_create, phone, status 
        FROM user 
        WHERE org_id IN (%s)
    """
    db.execute(sql, (tuple(org_ids),))
    result = db.cursor.fetchall()
    return result