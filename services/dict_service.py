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

def find_by_pid(pid):
    sql = "SELECT * FROM dict WHERE pid = %s"
    db.execute(sql, (pid,))
    result = db.cursor.fetchall()
    return result