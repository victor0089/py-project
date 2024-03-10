from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, role={self.role})"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name}, price={self.price})"

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    product = db.relationship('Product', backref=db.backref('sales', lazy=True))

    def __repr__(self):
        return f"Sale(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, date={self.date})"

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    sale = db.relationship('Sale', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f"Payment(id={self.id}, sale_id={self.sale_id}, amount={self.amount}, date={self.date})"
