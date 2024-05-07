import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
from logging.handlers import TimedRotatingFileHandler

# 创建 TimedRotatingFileHandler 对象，设置日志文件路径、文件名、存储周期等参数
file_handler = ConcurrentRotatingFileHandler('logs/my_log.log', maxBytes=1000000, backupCount=15, encoding='utf-8')

# 设置日志文件格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 创建或获取日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# 定义日志记录方法
def log_message(message, level=logging.INFO):
    # 记录日志消息
    logger.info(message)

