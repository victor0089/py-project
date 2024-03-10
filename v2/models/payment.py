from models import db

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    sale = db.relationship('Sale', backref=db.backref('payments', lazy=True))

    def __repr__(self):
        return f"Payment(id={self.id}, sales_id={self.sales_id}, amount={self.amount}, date={self.date})"
