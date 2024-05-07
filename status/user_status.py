from enum import Enum

class userStatus(Enum):
    OK = (1, "启用")
    FREEZED = (2, "冻结")
    DELETED = (3, "被删除")

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    @classmethod
    def value_of(cls, value: int) -> str:
        if value is None:
            return ""
        try:
            return cls(value).message
        except ValueError:
            return ""

    def get_code(self) -> int:
        return self.value[0]

    def get_message(self) -> str:
        return self.value[1]

    def set_code(self, code: int):
        raise AttributeError("Cannot modify an Enum member.")

    def set_message(self, message: str):
        raise AttributeError("Cannot modify an Enum member.")
