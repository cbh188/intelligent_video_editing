from utils.database import db
from services.config import PWDHASH_MODE,SALT_LENTH
from werkzeug.security import generate_password_hash, check_password_hash

def is_null(username, password):
    if(username == '' or password == ''):
        return True
    else:
        return False

def get_salt(username):
    sql = "SELECT salt FROM user WHERE account = %s"
    db.execute(sql, username)
    result = db.cursor.fetchone()
    salt = result['salt']
    return salt

def pwd_check(username,password):
    sql = "SELECT password FROM user WHERE account = %s AND status = 1"
    db.execute(sql, (username,))
    result = db.cursor.fetchone()
    pwd = result['password']
    # print(pwd)
    pwd_hash = PWDHASH_MODE + '$' + get_salt(username) + '$' + pwd  # 获得数据库中存的密码哈希值
    # print(pwd_hash)
    # print(check_password_hash(pwd_hash, password))
    if check_password_hash(pwd_hash, password):
        return True
    else:
        return False


def exist_user(username):
    sql = "SELECT * FROM user WHERE account = '%s'" % (username)
    db.execute(sql)
    result = db.cursor.fetchall()
    if(len(result) == 0):
        return False
    else:
        return True