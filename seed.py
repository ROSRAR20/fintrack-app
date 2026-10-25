from datetime import date
from app import create_app, db
from app.models import User, Transaction


def seed_database() -> None:
    """
    Populates the database with a default user and 15 realistic sample transactions
    across the current month so the dashboard and budget alert banner can be tested immediately.
    """
    app = create_app()

    with app.app_context():
        # Drop and recreate tables for a clean seed state
        db.drop_all()
        db.create_all()

        # 1. Create Default Demo User (monthly_budget = 50,000.0)
        demo_user = User(
            username="alex_morgan",
            email="alex.morgan@fintrack.io",
            monthly_budget=50000.0,
        )
        db.session.add(demo_user)
        db.session.flush()  # Obtain demo_user.id before inserting transactions

        today = date.today()
        year = today.year
        month = today.month

        def day_in_current_month(day_num: int) -> date:
            safe_day = min(day_num, 28)
            return date(year, month, safe_day)

        # 2. Create 15 Realistic Transactions across the current month
        # Total Expenses = $42,450.00 (84.9% of $50,000.00 budget -> triggers >= 80% Budget Alert!)
        sample_transactions = [
            Transaction(
                user_id=demo_user.id,
                amount=85000.00,
                category="Salary & Revenue",
                transaction_type="Income",
                transaction_date=day_in_current_month(1),
                description="Monthly Enterprise Consulting Retainer & SaaS Payout",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=14500.00,
                category="Housing & Rent",
                transaction_type="Expense",
                transaction_date=day_in_current_month(2),
                description="Commercial Studio & Executive Office Lease",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=6800.00,
                category="Software",
                transaction_type="Expense",
                transaction_date=day_in_current_month(3),
                description="AWS Production RDS MySQL & Cloud Compute Cluster",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=4200.00,
                category="Travel",
                transaction_type="Expense",
                transaction_date=day_in_current_month(5),
                description="Round-trip Flights & Hotel for FinTech Summit",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=1850.00,
                category="Utilities",
                transaction_type="Expense",
                transaction_date=day_in_current_month(6),
                description="Dedicated Fiber Optic Line & Electricity Bill",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=1420.00,
                category="Food & Dining",
                transaction_type="Expense",
                transaction_date=day_in_current_month(8),
                description="Client Executive Dinner at Nobu Downtown",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=3400.00,
                category="Shopping",
                transaction_type="Expense",
                transaction_date=day_in_current_month(10),
                description="Ergonomic Herman Miller Workstations (2 Units)",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=2150.00,
                category="Software",
                transaction_type="Expense",
                transaction_date=day_in_current_month(11),
                description="GitHub Enterprise, Datadog APM & Sentry Annual Seats",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=640.00,
                category="Food & Dining",
                transaction_type="Expense",
                transaction_date=day_in_current_month(13),
                description="Team Engineering Sprint Catering & Coffee Supply",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=2900.00,
                category="Travel",
                transaction_type="Expense",
                transaction_date=day_in_current_month(15),
                description="Regional Client On-Site Architecture Workshop Transit",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=920.00,
                category="Utilities",
                transaction_type="Expense",
                transaction_date=day_in_current_month(17),
                description="Cloud Backup Bandwidth & Corporate Mobile Plans",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=1750.00,
                category="Shopping",
                transaction_type="Expense",
                transaction_date=day_in_current_month(19),
                description="4K Ultrawide Monitors & Thunderbolt Docks",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=480.00,
                category="Food & Dining",
                transaction_type="Expense",
                transaction_date=day_in_current_month(21),
                description="Board Advisory Working Lunch",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=1440.00,
                category="Software",
                transaction_type="Expense",
                transaction_date=day_in_current_month(23),
                description="OpenAI API Credits & Snowflake Data Warehouse Usage",
            ),
            Transaction(
                user_id=demo_user.id,
                amount=12500.00,
                category="Salary & Revenue",
                transaction_type="Income",
                transaction_date=day_in_current_month(24),
                description="Quarterly Performance Milestone Bonus",
            ),
        ]

        db.session.add_all(sample_transactions)
        db.session.commit()

        print("============================================================")
        print("FinTrack Database Seeded Successfully!")
        print(f"User: {demo_user.username} ({demo_user.email})")
        print(f"Monthly Budget: ${demo_user.monthly_budget:,.2f}")
        print(f"Inserted {len(sample_transactions)} sample transactions for {year}-{month:02d}.")
        print("============================================================")


if __name__ == "__main__":
    seed_database()
