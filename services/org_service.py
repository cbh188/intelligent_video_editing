from utils.database import db
def query_all_node(my_org_id):
    org_list = query_all_sub(my_org_id)
    # print("orglist:", org_list)
    result = generate_tree(org_list, my_org_id)
    return result

def query_all_sub(my_org_id):
    sql = ("WITH RECURSIVE organization_tree AS "
           "(SELECT * FROM organization WHERE id = %s "
           "UNION ALL SELECT child.*  FROM organization child JOIN organization_tree parent "
           "ON child.pid = parent.id) SELECT o1.*, ( CASE WHEN (o2.id = 0 OR o2.id IS NULL) THEN NULL ELSE o2.name END ) AS pname "
           "FROM organization_tree o1 LEFT JOIN organization o2 ON o1.pid = o2.id WHERE o1.is_deleted = 0 ORDER BY o1.num;")
    db.execute(sql, (my_org_id,))
    result = db.cursor.fetchall()
    return result
def generate_tree(org_list, my_org_id):
    result = []
    org_map = {org['id']: org for org in org_list}
    for org_node in org_map.values():
        org_node['children'] = []
    for org_node in org_map.values():
        if org_node['pid'] != 0 and org_node['id'] != my_org_id:
            parent_node = org_map.get(org_node['pid'])
            # if parent_node is not None:
                # if 'children' not in parent_node:
                #     parent_node['children'] = []
            parent_node['children'].append(org_node)
        else:
            result.append(org_node)
    # print(result)
    return result

def query_all():
    sql = "SELECT * FROM organization WHERE is_deleted = '0' ORDER BY num"
    db.execute(sql)
    result = db.cursor.fetchall()
    return result

def find_org_by_code(org_code):
    sql = "SELECT * FROM organization WHERE org_code = %s"
    db.execute(sql, (org_code,))
    result = db.cursor.fetchone()
    return result

def get_pids(id):
    sql = ("WITH RECURSIVE ParentCTE AS (SELECT id, pid FROM organization WHERE id = %s UNION ALL SELECT t.id, t.pid "
           "FROM organization t INNER JOIN ParentCTE p ON t.id = p.pid) "
           "SELECT CONCAT(GROUP_CONCAT(CONCAT('[', pid, ']') ORDER BY pid), ',') AS pids FROM ParentCTE;")
    db.execute(sql, (id,))
    result = db.cursor.fetchone()
    print(result)
    return result['pids']