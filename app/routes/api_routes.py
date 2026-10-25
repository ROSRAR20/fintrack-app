from datetime import datetime, date
import calendar
from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app import db
from app.models import User, Transaction

api_bp = Blueprint("api", __name__)

ALLOWED_TRANSACTION_TYPES = {"Expense", "Income"}


def get_or_create_default_user() -> User:
    """
    Retrieves the primary demo user (id=1) or creates a default user if the DB is empty.
    """
    user = User.query.first()
    if not user:
        user = User(
            username="alex_morgan",
            email="alex.morgan@fintrack.io",
            monthly_budget=50000.0,
        )
        db.session.add(user)
        db.session.commit()
    return user


def parse_iso_date(date_str: str) -> date | None:
    """Strictly validates and parses a date string in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def get_month_date_bounds(month_str: str | None) -> tuple[date, date] | None:
    """
    Given a YYYY-MM string, returns (first_day_of_month, last_day_of_month).
    Allows range queries that leverage the composite index on (user_id, transaction_date).
    """
    if not month_str:
        return None
    try:
        dt = datetime.strptime(month_str.strip(), "%Y-%m")
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        start_date = date(dt.year, dt.month, 1)
        end_date = date(dt.year, dt.month, last_day)
        return start_date, end_date
    except ValueError:
        return None


@api_bp.route("/transactions", methods=["GET"])
def get_transactions():
    """
    GET /api/transactions
    Supports optional query parameters: ?category=<category>&month=<YYYY-MM>
    Returns a JSON list of matching transactions ordered by transaction_date descending.
    """
    user = get_or_create_default_user()
    category_filter = request.args.get("category", "").strip()
    month_filter = request.args.get("month", "").strip()

    query = Transaction.query.filter(Transaction.user_id == user.id)

    if category_filter and category_filter.lower() != "all":
        query = query.filter(Transaction.category == category_filter)

    if month_filter:
        bounds = get_month_date_bounds(month_filter)
        if not bounds:
            return jsonify({
                "error": "Invalid month parameter format. Expected YYYY-MM (e.g., 2026-10)."
            }), 400
        start_date, end_date = bounds
        query = query.filter(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )

    transactions = query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.id.desc(),
    ).all()

    return jsonify([tx.to_dict() for tx in transactions]), 200


@api_bp.route("/transactions", methods=["POST"])
def create_transaction():
    """
    POST /api/transactions
    Validates JSON payload and creates a new transaction record.
    Returns HTTP 201 with created record or HTTP 400 with {"error": "..."}.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON request body."}), 400

    # Validate amount (> 0)
    raw_amount = data.get("amount")
    if raw_amount is None or isinstance(raw_amount, bool):
        return jsonify({"error": "Field 'amount' is required and must be a positive number."}), 400
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Field 'amount' must be a valid numeric value."}), 400

    if amount <= 0:
        return jsonify({"error": "Field 'amount' must be greater than zero (> 0)."}), 400

    # Validate category
    category = str(data.get("category", "")).strip()
    if not category:
        return jsonify({"error": "Field 'category' is required and cannot be empty."}), 400
    if len(category) > 64:
        return jsonify({"error": "Field 'category' cannot exceed 64 characters."}), 400

    # Validate transaction_date (YYYY-MM-DD)
    raw_date = data.get("transaction_date")
    if not raw_date:
        return jsonify({"error": "Field 'transaction_date' is required in YYYY-MM-DD format."}), 400
    parsed_date = parse_iso_date(str(raw_date))
    if not parsed_date:
        return jsonify({"error": "Field 'transaction_date' must be a valid date in YYYY-MM-DD format."}), 400

    # Validate transaction_type ('Expense' or 'Income')
    transaction_type = str(data.get("transaction_type", "Expense")).strip()
    if transaction_type not in ALLOWED_TRANSACTION_TYPES:
        return jsonify({
            "error": "Field 'transaction_type' must be either 'Expense' or 'Income'."
        }), 400

    # Validate description (max 255 chars)
    description = str(data.get("description", "") or "").strip()
    if len(description) > 255:
        return jsonify({"error": "Field 'description' cannot exceed 255 characters."}), 400

    user = get_or_create_default_user()

    new_tx = Transaction(
        user_id=user.id,
        amount=round(amount, 2),
        category=category,
        transaction_type=transaction_type,
        transaction_date=parsed_date,
        description=description,
    )

    db.session.add(new_tx)
    db.session.commit()

    return jsonify(new_tx.to_dict()), 201


@api_bp.route("/transactions/<int:tx_id>", methods=["PUT"])
def update_transaction(tx_id: int):
    """
    PUT /api/transactions/<int:id>
    Updates an existing transaction's amount, category, transaction_type, date, or description.
    Returns HTTP 200 on success, HTTP 400 on validation error, or HTTP 404 if not found.
    """
    transaction = db.session.get(Transaction, tx_id)
    if not transaction:
        return jsonify({"error": f"Transaction with id {tx_id} was not found."}), 404

    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON request body."}), 400

    if "amount" in data:
        raw_amount = data.get("amount")
        if raw_amount is None or isinstance(raw_amount, bool):
            return jsonify({"error": "Field 'amount' must be a positive number."}), 400
        try:
            amount = float(raw_amount)
        except (ValueError, TypeError):
            return jsonify({"error": "Field 'amount' must be a valid numeric value."}), 400
        if amount <= 0:
            return jsonify({"error": "Field 'amount' must be greater than zero (> 0)."}), 400
        transaction.amount = round(amount, 2)

    if "category" in data:
        category = str(data.get("category", "")).strip()
        if not category:
            return jsonify({"error": "Field 'category' cannot be empty."}), 400
        if len(category) > 64:
            return jsonify({"error": "Field 'category' cannot exceed 64 characters."}), 400
        transaction.category = category

    if "transaction_date" in data:
        parsed_date = parse_iso_date(str(data.get("transaction_date", "")))
        if not parsed_date:
            return jsonify({
                "error": "Field 'transaction_date' must be a valid date in YYYY-MM-DD format."
            }), 400
        transaction.transaction_date = parsed_date

    if "transaction_type" in data:
        tx_type = str(data.get("transaction_type", "")).strip()
        if tx_type not in ALLOWED_TRANSACTION_TYPES:
            return jsonify({
                "error": "Field 'transaction_type' must be either 'Expense' or 'Income'."
            }), 400
        transaction.transaction_type = tx_type

    if "description" in data:
        description = str(data.get("description", "") or "").strip()
        if len(description) > 255:
            return jsonify({"error": "Field 'description' cannot exceed 255 characters."}), 400
        transaction.description = description

    db.session.commit()
    return jsonify(transaction.to_dict()), 200


@api_bp.route("/transactions/<int:tx_id>", methods=["DELETE"])
def delete_transaction(tx_id: int):
    """
    DELETE /api/transactions/<int:id>
    Deletes a transaction by ID and returns HTTP 200 confirmation or HTTP 404 if not found.
    """
    transaction = db.session.get(Transaction, tx_id)
    if not transaction:
        return jsonify({"error": f"Transaction with id {tx_id} was not found."}), 404

    db.session.delete(transaction)
    db.session.commit()

    return jsonify({
        "message": f"Transaction {tx_id} deleted successfully.",
        "deleted_id": tx_id,
    }), 200


@api_bp.route("/summary", methods=["GET"])
def get_summary():
    """
    GET /api/summary
    Executes database-level aggregation using SQLAlchemy func.sum() and .group_by(Transaction.category).
    Supports optional ?month=<YYYY-MM> query parameter (defaults to the current month or latest active month).
    """
    user = get_or_create_default_user()
    month_param = request.args.get("month", "").strip()

    # Base filter for database-level expense aggregation
    expense_filters = [
        Transaction.user_id == user.id,
        Transaction.transaction_type == "Expense",
    ]
    income_filters = [
        Transaction.user_id == user.id,
        Transaction.transaction_type == "Income",
    ]

    if month_param:
        bounds = get_month_date_bounds(month_param)
        if not bounds:
            return jsonify({
                "error": "Invalid month parameter format. Expected YYYY-MM."
            }), 400
        start_date, end_date = bounds
        expense_filters.extend([
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        ])
        income_filters.extend([
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        ])

    # Database-level aggregation by category using SQLAlchemy func.sum() and .group_by()
    category_rows = (
        db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0.0).label("total"),
        )
        .filter(*expense_filters)
        .group_by(Transaction.category)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    # Database-level total expense sum
    total_spent_scalar = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(*expense_filters)
        .scalar()
    )
    total_spent = round(float(total_spent_scalar or 0.0), 2)

    # Database-level total income sum
    total_income_scalar = (
        db.session.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(*income_filters)
        .scalar()
    )
    total_income = round(float(total_income_scalar or 0.0), 2)

    monthly_budget = round(float(user.monthly_budget), 2)
    remaining_budget = round(monthly_budget - total_spent, 2)
    budget_utilization_percent = (
        round((total_spent / monthly_budget) * 100.0, 2)
        if monthly_budget > 0
        else 0.0
    )

    category_breakdown = [
        {
            "category": row.category,
            "total": round(float(row.total), 2),
        }
        for row in category_rows
    ]

    return jsonify({
        "total_spent": total_spent,
        "total_income": total_income,
        "monthly_budget": monthly_budget,
        "remaining_budget": remaining_budget,
        "budget_utilization_percent": budget_utilization_percent,
        "budget_alert": bool(budget_utilization_percent >= 80.0),
        "category_breakdown": category_breakdown,
    }), 200


@api_bp.route("/budget", methods=["PUT"])
def update_budget():
    """
    PUT /api/budget
    Updates the user's monthly_budget threshold with validation (budget > 0).
    Accepts {"monthly_budget": <number>} or {"budget": <number>}.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON request body."}), 400

    raw_budget = data.get("monthly_budget", data.get("budget"))
    if raw_budget is None or isinstance(raw_budget, bool):
        return jsonify({
            "error": "Field 'monthly_budget' is required and must be greater than zero."
        }), 400

    try:
        new_budget = float(raw_budget)
    except (ValueError, TypeError):
        return jsonify({"error": "Field 'monthly_budget' must be a valid numeric value."}), 400

    if new_budget <= 0:
        return jsonify({"error": "Monthly budget must be greater than zero (> 0)."}), 400

    user = get_or_create_default_user()
    user.monthly_budget = round(new_budget, 2)
    db.session.commit()

    return jsonify({
        "message": "Monthly budget updated successfully.",
        "monthly_budget": user.monthly_budget,
        "user": user.to_dict(),
    }), 200
