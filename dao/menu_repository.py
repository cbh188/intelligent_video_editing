from utils.database import db
def get_menus_by_roleIds(roleIds):
    sql = ("SELECT m1.id AS id,m1.icon AS icon,( CASE WHEN ( m2.id = 0 OR m2.id IS NULL ) THEN 0 ELSE m2.id END ) AS parentId, "
           "m1.NAME AS NAME,m1.url AS url,m1.levels AS levels,m1.ismenu AS ismenu,m1.num AS num,m1.CODE AS CODE,m1.component,m1.hidden "
           "FROM menu m1 LEFT JOIN menu m2 ON m1.pcode = m2.CODE "
           "WHERE m1.id IN (SELECT DISTINCT ( menu_id ) FROM role_rel_menu WHERE role_id IN ( %s )) "
           "ORDER BY levels,num ASC")
    db.execute(sql, (roleIds,))
    result = db.cursor.fetchall()
    return result

def query_menus_by_roleIds(roleIds):
    sql = "SELECT m.* FROM menu m JOIN role_rel_menu rrm ON m.id = rrm.menu_id WHERE rrm.role_id IN ( %s )"
    db.execute(sql, (roleIds,))
    result = db.cursor.fetchall()
    return result

def get_menus():
    sql = ("SELECT m1.id AS id, m1.icon AS icon, ( CASE WHEN (m2.id = 0 OR m2.id IS NULL) THEN 0 ELSE m2.id END ) AS parentId, "
           "m1. NAME AS NAME, m1.url AS url, m1.levels AS levels, m1.ismenu AS ismenu, m1.num AS num, m1. CODE AS CODE,m1.component,m1.hidden,"
           "m1.pcode FROM menu m1 LEFT JOIN menu m2 ON m1.pcode = m2. CODE ORDER BY levels, num ASC")
    db.execute(sql)
    result = db.cursor.fetchall()
    return result