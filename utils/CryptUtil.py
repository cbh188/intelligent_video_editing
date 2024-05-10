import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


# 定义常量
KEY = "cbh188.handsome."
IV = "1234567890123456"


def encode_base64(bytes_data):
    encoded = base64.b64encode(bytes_data).decode('utf-8')
    return encoded.replace('\n', '')


def encrypt(data: str, key: str = KEY, iv: str = IV) -> str:
    try:
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))

        encrypted = cipher.encrypt(data.encode('utf-8'))

        return base64.b64encode(encrypted).decode('utf-8')  # 使用base64.b64encode并转为字符串
    except Exception as e:
        print(e)
        return "encrypt error:{}".format(e)



def decrypt(data: str, key: str = KEY, iv: str = IV) -> str:
    try:
        encrypted_data = base64.b64decode(data)

        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        decrypted_data = cipher.decrypt(encrypted_data)

        # 去除填充
        decrypted_data = decrypted_data[:-decrypted_data[-1]]

        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(e)
        return "decrypt error:{}".format(e)


def default_encrypt(data: str) -> str:
    return encrypt(data)


def default_decrypt(data: str) -> str:
    return decrypt(data)
