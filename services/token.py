from dao import token
class RevokedTokenModel:
    def __init__(self,jti):
        self.id: int = None
        self.jti: str = jti

    def add(self):
        token.add_into_blacklist(self.jti)

    @classmethod
    def is_jti_blacklisted(cls, jti):
        if token.get_by_jti(jti) is not None:
            return True
        else:
            return False