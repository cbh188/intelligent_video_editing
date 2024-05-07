from utils.database import db

def build_fuzzy_search_conditions(column_name, value):
    if value:
        like_pattern = f'%{value}%'
        return f"{column_name} LIKE '%s'", like_pattern
    else:
        return "", None

def query_page(query, page_num, page_size):
    offset = (page_num - 1) * page_size
    query += f" LIMIT {page_size} OFFSET {offset}"
    # print(query)
    db.execute(query)
    result = db.cursor.fetchall()
    return result

def find_my_org_id(account):
    sql = "SELECT org_id FROM user WHERE account = %s"
    db.execute(sql, (account,))
    result = db.cursor.fetchone()
    return result