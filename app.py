from flask import Flask
from mkad_blueprint.mkad_blueprint import mkad_bp

app = Flask(__name__)
app.register_blueprint(mkad_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
