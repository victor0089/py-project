from flask import Flask
from flask_session import Session
from views.auth import auth_bp
from views.products import products_bp
from views.sales import sales_bp
from models import db

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure secret key

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(products_bp)
app.register_blueprint(sales_bp)

if __name__ == '__main__':
    app.run(debug=True)
