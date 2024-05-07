from utils.database import db
def add_into_blacklist(jti):
    sql = "insert into revoked_token (jti) VALUES (%s)"
    db.execute(sql, (jti,))
    return True

def get_by_jti(jti):
    sql = "select * from revoked_token where jti = %s"
    db.execute(sql, (jti,))
    result = db.cursor.fetchone()
    return result