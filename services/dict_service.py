from datetime import datetime

from services import base_service
from utils.database import db

def get_dicts_by_pname(dict_name):
    sql = "SELECT * FROM dict WHERE pid IN (SELECT id FROM dict WHERE name = %s)"
    db.execute(sql, (dict_name,))
    result = db.cursor.fetchall()
    return result

def find_by_name_like(dict_name):
    sql = "SELECT * FROM dict WHERE name LIKE %s"
    db.execute(sql, ("%" + dict_name + "%", ))
    result = db.cursor.fetchall()
    return result

def find_by_name(dict_name):
    sql = "SELECT * FROM dict WHERE name = %s"
    db.execute(sql, (dict_name,))
    result = db.cursor.fetchone()
    return result

def find_by_pid(pid):
    sql = "SELECT * FROM dict WHERE pid = %s"
    db.execute(sql, (pid,))
    result = db.cursor.fetchall()
    return result

def find_by_name_pid(dict_name, pid):
    sql = "SELECT * FROM dict WHERE name = %s AND pid = %s"
    db.execute(sql, (dict_name, pid))
    result = db.cursor.fetchall()
    return result

def delete_dict(dict_ids):
    if isinstance(dict_ids, list):
        dict_ids = [int(dict_id) for dict_id in dict_ids]
    else:
        dict_ids = [dict_ids]
    if len(dict_ids) == 1:
        sql = "DELETE FROM dict WHERE id = {} OR pid = {}".format(dict_ids[0], dict_ids[0])
    else:
        sql = "DELETE FROM dict WHERE id IN {} OR pid IN {}".format(tuple(dict_ids), tuple(dict_ids))
    db.execute(sql)
    result = db.cursor.rowcount
    return result

def add_dict(dict_name, dict_values, user_id):

    # 解析字典值
    pairs = dict_values.split(";")[:-1]
    value_dict = {}
    # print(pairs)
    for pair in pairs:
        key, value = pair.split(":")
        value_dict[key] = value
    num = 0
    pid = 0
    # 添加字典
    create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = ("INSERT INTO dict (create_by, create_time, name, num, pid)"
           'VALUES (%s, %s, %s, %s, %s)')

    params = [user_id, create_time, dict_name, num, pid]

    base_service.insert(sql, params)
    # print(value_dict)
    # 添加字典值
    for key, value in value_dict.items():
        num = key
        print(num)
        name = value
        print(name)
        pid = find_by_name(dict_name)['id']
        print(pid)
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = ("INSERT INTO dict (create_by, create_time, name, num, pid)"
               "VALUES (%s, %s, %s, %s, %s)")
        params = [user_id, create_time, name, num, pid]
        print(sql)
        base_service.insert(sql, params)