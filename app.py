from flask import Flask, jsonify, request, render_template
from utils.database import db
from utils.response_utils import handle_errors, success_response, error_response
from views.account import account_bp
from views.user import user_bp
from views.organization import org_bp
from views.dict import dict_bp
from views.student import student_bp
from views.video import video_bp
from views.role import role_bp
from views.menu import menu_bp
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager, get_jwt
from flask_cors import CORS
from datetime import timedelta
from services.token import RevokedTokenModel
from utils.log import log_message

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'my_secret_key'
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config['JWT_BLACKLIST_ENABLED'] = True  # enable blacklist feature
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']  # allow blacklisting for access and refresh tokens
jwt = JWTManager(app)

# 注册蓝图
app.register_blueprint(account_bp)
app.register_blueprint(user_bp)
app.register_blueprint(org_bp)
app.register_blueprint(dict_bp)
app.register_blueprint(student_bp)
app.register_blueprint(video_bp)
app.register_blueprint(role_bp)
app.register_blueprint(menu_bp)

# 解决跨域问题
CORS(app, supports_credentials=True)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, decrypted_token):
    jti = decrypted_token['jti']
    return RevokedTokenModel.is_jti_blacklisted(jti)

@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    print(jti)
    try:
        revoked_token = RevokedTokenModel(jti=jti)
        revoked_token.add()
        return jsonify(success_response(data="成功退出", path=request.url))
    except Exception as e:
        log_message(e)
        return error_response(400, 40005, str(e), "未知错误,退出失败")

@app.route('/')
def hello_world():  # put application's code here
    return render_template('index.html')

@handle_errors
@app.route('/read_image', methods=['POST','GET'])
def read_image():
    image, image_base64 = db.read_image(1)
    return jsonify(success_response(data=image_base64, path=request.path))

@app.route('/hello', methods=['POST','GET'])
def hello():
    return jsonify(success_response(data='hello world', path=request.path))

if __name__ == '__main__':
    app.run()
