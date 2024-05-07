import base64
import io
import pymysql
from PIL import Image
from io import BytesIO
from utils.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_CHARSET
import threading
lock = threading.Lock()
class MysqlDb:
    def __init__(self, host, port, user, passwd, db, charset):
        # 建立数据库连接
        self.conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            passwd=passwd,
            db=db,
            charset=charset,
            autocommit=True
        )
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    def __del__(self):
        # 关闭游标
        if self.cursor is not None:
            self.cursor.close()
        # 关闭数据库连接
        if self.conn is not None:
            self.conn.close()

    # 执行操作
    def execute(self, sql, params=None):
        try:
            # 检查连接是否断开，如果断开就进行重连
            lock.acquire()
            self.conn.ping(reconnect=True)
            self.cursor.execute(sql, params)
            lock.release()
        except Exception as e:
            print(f"Error executing SQL: {e}")
            self.conn.rollback()
            return "数据库操作出现错误"

    # 根据学生id读取照片
    def read_image(self, student_id):
        sql = "SELECT image FROM student WHERE student_id = %s"
        self.execute(sql, (student_id,))
        image_data = self.cursor.fetchone()['image']
        image = Image.open(BytesIO(image_data))
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        return image, image_base64

    # 将图像数据转换为 Base64 编码的字符串
    def image_to_base64(self, image):
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 读取视频
    def read_video(self, video_id):
        try:
            sql = "SELECT video_content FROM video WHERE video_id = %s"
            self.execute(sql, (video_id,))
            video_data = self.cursor.fetchone()['video_content']
            return video_data
        except Exception as e:
            print(f"Error reading video: {e}")
            return None

    # 按照创建时间范围查找视频
    def get_videos_by_time_range(self, start_time, end_time):
        try:
            sql = "SELECT video_content FROM video WHERE upload_time BETWEEN %s AND %s"
            self.execute(sql, (start_time, end_time))
            videos = self.cursor.fetchall()
            for video in videos:
                video['base64'] = base64.b64encode(video['video_content']).decode('utf-8')
            return videos
        except Exception as e:
            print(f"Error getting videos by time range: {e}")
            return None



db = MysqlDb(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_CHARSET)