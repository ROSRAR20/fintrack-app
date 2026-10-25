from datetime import date
from flask import Blueprint, render_template
from app.models import User
from app.routes.api_routes import get_or_create_default_user

web_bp = Blueprint("web", __name__)

DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Utilities",
    "Travel",
    "Software",
    "Shopping",
    "Housing & Rent",
    "Salary & Revenue",
]


@web_bp.route("/", methods=["GET"])
def index():
    """
    Renders the responsive single-page FinTrack dashboard via Jinja2 template.
    """
    user: User = get_or_create_default_user()
    current_month = date.today().strftime("%Y-%m")
    today_iso = date.today().isoformat()

    return render_template(
        "index.html",
        user=user,
        categories=DEFAULT_CATEGORIES,
        current_month=current_month,
        today_iso=today_iso,
    )
