from utils.database import db
def query_roles(role_id):
    # print(org_ids)
    # print(tuple(org_ids))
    sql = f"""
                WITH RECURSIVE subroles AS (
            SELECT role_id, name, code, org_id, num, gmt_create, pid
            FROM role
            WHERE role_id = {role_id}
            
            UNION ALL
            
            SELECT r.role_id, r.name, r.code, r.org_id, r.num, r.gmt_create, r.pid
            FROM role r
            JOIN subroles s ON r.pid = s.role_id
        )
        SELECT s.role_id AS id, s.name, s.code, s.org_id AS orgId, s.num, s.gmt_create AS createTime,
               s.pid, (CASE WHEN (r.role_id IS NULL OR r.role_id = 0) THEN NULL ELSE r.name END) AS pName
        FROM subroles s
        LEFT JOIN role r ON s.pid = r.role_id
        ORDER BY s.num
            """
    # print(sql)
    db.execute(sql)
    result = db.cursor.fetchall()
    return result

def get_role_by_id(role_id):
    sql = "SELECT * FROM role WHERE role_id = %s"
    db.execute(sql, (role_id,))
    result = db.cursor.fetchone()
    return result

def find_role_by_code(code):
    sql = "SELECT * FROM role WHERE code = %s"
    db.execute(sql, (code,))
    result = db.cursor.fetchone()
    return result