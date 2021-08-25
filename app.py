from flask import Flask
from mkad_blueprint import mkad_bp

app = Flask(__name__)
app.register_blueprint(mkad_bp)
