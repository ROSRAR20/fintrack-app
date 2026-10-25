from datetime import date
from app import db


class User(db.Model):
    """
    User account model storing profile details and monthly budget threshold.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    monthly_budget = db.Column(db.Float, nullable=False, default=50000.0)

    # One-to-many relationship: a user has many transactions
    transactions = db.relationship(
        "Transaction",
        backref="user",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """Serialize User model instance to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "monthly_budget": round(float(self.monthly_budget), 2),
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} budget={self.monthly_budget}>"


class Transaction(db.Model):
    """
    Financial transaction record linked to a User.
    Includes single-column and composite B-Tree indexes for query optimization.
    """
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True)
    transaction_type = db.Column(
        db.String(20), nullable=False, default="Expense"
    )
    transaction_date = db.Column(
        db.Date, nullable=False, default=date.today, index=True
    )
    description = db.Column(db.String(255), nullable=True, default="")

    # Explicit database indexes for high-performance filtering and aggregation:
    # 1. Composite index on (user_id, transaction_date) for date-range & monthly ledger queries
    # 2. Index on category for fast GROUP BY and category filtering
    __table_args__ = (
        db.Index("ix_transactions_user_date", "user_id", "transaction_date"),
        db.Index("ix_transactions_category", "category"),
    )

    def to_dict(self) -> dict:
        """Serialize Transaction model instance to a JSON-compatible dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": round(float(self.amount), 2),
            "category": self.category,
            "transaction_type": self.transaction_type,
            "transaction_date": (
                self.transaction_date.isoformat()
                if isinstance(self.transaction_date, date)
                else str(self.transaction_date)
            ),
            "description": self.description or "",
        }

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.transaction_type!r} "
            f"category={self.category!r} amount={self.amount} date={self.transaction_date}>"
        )
