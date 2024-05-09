import logging
from functools import wraps
from flask import jsonify
from werkzeug.exceptions import Forbidden, Unauthorized

from utils.log import log_message

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Forbidden as e:
            # 服务器拒绝请求
            log_message('403 Forbidden', level=logging.ERROR)
            return forbidden_response(errorCode=1005, errorMessage="403 Forbidden")
        except Unauthorized as e:
            # 请求要求身份验证
            log_message('401 Unauthorized', level=logging.ERROR)
            return unauthorized_response(errorCode=1004, errorMessage="401 Unauthorized")
        except FileNotFoundError as e:
            # 文件未找到错误
            log_message(f'File not found: {str(e)}', level=logging.ERROR)
            return not_found_response(errorCode=1002, errorMessage="File not found")
        except ValueError as e:
            # 值错误
            log_message(f'Value error: {str(e)}', level=logging.ERROR)
            return jsonify(error_response(status_code=400, errorCode=1003, errorMessage="Value error", userMessage="Invalid request"))
        except Exception as e:
            # 其他系统异常
            log_message(f'An error occurred: {str(e)}', level=logging.ERROR)
            return internal_server_error_response(errorCode=1001, errorMessage="An error occurred")
    return wrapper
def error_response(status_code, errorCode, errorMessage, userMessage):
    response = {
        "code": status_code,
        "status": "error",
        "errorCode": errorCode,
        "errorMessage": errorMessage,
        "msg": userMessage
    }
    return response

def success_response(data=None, path=None):
    response = {
        "code": 200,
        "message": "操作成功",
        "data": data
    }
    # 构建日志消息
    message = f'成功处理请求: {path}' if path else '操作成功'
    # 写入日志
    log_message(message, level=logging.INFO)
    return response

def expire():
    response = {
        "code": 50014,
        "message": "Token过期",
        "data": None
    }
    return response
def unauthorized_response(errorCode, errorMessage):
    return error_response(401, errorCode, errorMessage, "Unauthorized")

def forbidden_response(errorCode, errorMessage):
    return error_response(403, errorCode, errorMessage, "Forbidden")

def not_found_response(errorCode, errorMessage):
    return error_response(404, errorCode, errorMessage, "Not Found")

def internal_server_error_response(errorCode, errorMessage):
    return error_response(500, errorCode, errorMessage, "服务异常")

