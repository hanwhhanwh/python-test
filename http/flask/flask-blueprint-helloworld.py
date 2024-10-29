# Flask HelloWorld
# author : hbesthee@naver.com
# date : 2024-10-29

from flask import Flask, Blueprint, render_template

app = Flask(__name__)

# Blueprint 정의
main_bp = Blueprint('main', __name__, url_prefix = '/', template_folder = './')

@main_bp.route('/')
def index():
    return render_template('flask-blueprint-helloworld.html', message='Hello, World!')

# Blueprint 등록
app.register_blueprint(main_bp)

if (__name__ == '__main__'):
    app.run()