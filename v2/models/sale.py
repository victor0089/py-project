from datetime import datetime
from models import db

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"Sale(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, date={self.date})"
