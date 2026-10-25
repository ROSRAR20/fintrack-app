# FinTrack: Expense & Transaction Management System

A modular, production-ready full-stack expense and transaction management web application built with **Python (Flask)**, **SQLAlchemy ORM** (configured for **MySQL** with automatic **SQLite** fallback), **Jinja2**, **HTML5/CSS3**, and **Vanilla JavaScript (Fetch API)**.

---

## 1. Architecture & Folder Structure

FinTrack enforces the **Flask Application Factory Pattern** and modular **Blueprints** to separate RESTful JSON API controllers from Jinja2 HTML view routes:

```text
fintrack-app/
├── app/
│   ├── __init__.py          # App factory, DB initialization, Blueprint registration
│   ├── models.py            # SQLAlchemy models with composite & single-column indexes
│   ├── routes/
│   │   ├── api_routes.py    # RESTful JSON API Blueprint (/api/...)
│   │   └── web_routes.py    # Frontend Jinja2 view Blueprint (/)
│   ├── static/
│   │   ├── css/style.css    # Clean, modern fintech dashboard styling
│   │   └── js/main.js       # Fetch API logic for dynamic UI updates without page reload
│   └── templates/
│       └── index.html       # Responsive dashboard with summary cards, budget alert banner, form & table
├── seed.py                  # Script to populate DB with default user & 15 realistic sample transactions
├── requirements.txt         # Required Python packages
├── README.md                # Documentation, database schema & REST API specification
└── run.py                   # Application entry point
```

---

## 2. Database Schema & Query Optimization

Defined in `app/models.py` using `Flask-SQLAlchemy`:

### `users` Table (`User` Model)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | `PRIMARY KEY, AUTOINCREMENT` | Unique user identifier |
| `username` | `String(80)` | `UNIQUE, NOT NULL` | Account handle |
| `email` | `String(120)` | `UNIQUE, NOT NULL` | User email address |
| `monthly_budget` | `Float` | `NOT NULL, DEFAULT 50000.0` | Monthly expense cap threshold |

### `transactions` Table (`Transaction` Model)
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | `PRIMARY KEY, AUTOINCREMENT` | Unique transaction identifier |
| `user_id` | `Integer` | `FOREIGN KEY (users.id), NOT NULL` | Owning user reference |
| `amount` | `Float` | `NOT NULL` | Positive transaction value (`> 0`) |
| `category` | `String(64)` | `NOT NULL, INDEXED` | Category (`Food & Dining`, `Software`, etc.) |
| `transaction_type` | `String(20)` | `NOT NULL, DEFAULT 'Expense'` | `'Expense'` or `'Income'` |
| `transaction_date` | `Date` | `NOT NULL, INDEXED` | ISO `YYYY-MM-DD` date |
| `description` | `String(255)` | `NULLABLE` | Optional transaction memo |

### Database Indexing Strategy
1. **Composite Index `ix_transactions_user_date` on `(user_id, transaction_date)`**: Optimizes monthly date-range filtering and chronological `ORDER BY transaction_date DESC` queries without full table scans.
2. **Single-Column Index `ix_transactions_category` on `(category)`**: Accelerates `GROUP BY category` aggregations in `GET /api/summary` and category filtering in `GET /api/transactions`.

---

## 3. Quick Start & Setup Instructions

### Prerequisites
- Python 3.10+
- Optional: MySQL 8.0+ server (defaults to local SQLite `fintrack.db` out of the box)

### Step 1: Clone & Create Virtual Environment
```bash
cd fintrack-app
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Database Connection (Optional MySQL)
By default, FinTrack runs out of the box using SQLite (`sqlite:///fintrack.db`). To connect to MySQL:
```bash
export DATABASE_URL="mysql+pymysql://user:password@localhost/fintrack_db"
```

### Step 3: Seed the Database with Demo Data
Run `seed.py` to create the tables, indexes, default user (`alex_morgan`), and 15 realistic transactions for the current month:
```bash
python seed.py
```

### Step 4: Start the Application Server
```bash
python run.py
```
Open `http://localhost:5000` in your browser.

---

## 4. RESTful API Specification

### `1. GET /api/transactions`
Returns transactions ordered by `transaction_date` descending.
- **Query Parameters**:
  - `category` (optional): e.g. `Software`, `Food & Dining`
  - `month` (optional): `YYYY-MM` format, e.g. `2026-10`
- **Response (`200 OK`)**:
```json
[
  {
    "id": 14,
    "user_id": 1,
    "amount": 1440.0,
    "category": "Software",
    "transaction_type": "Expense",
    "transaction_date": "2026-10-23",
    "description": "OpenAI API Credits & Snowflake Data Warehouse Usage"
  }
]
```

### `2. POST /api/transactions`
Creates a new transaction after validating `amount > 0`, non-empty `category`, valid `YYYY-MM-DD` date, and `description <= 255` chars.
- **Request Body**:
```json
{
  "amount": 250.00,
  "category": "Software",
  "transaction_type": "Expense",
  "transaction_date": "2026-10-25",
  "description": "Cloudflare Pro Plan"
}
```
- **Responses**: `201 Created` with created object, or `400 Bad Request` with `{"error": "Detailed validation message"}`.

### `3. PUT /api/transactions/<int:id>`
Updates an existing transaction by ID.
- **Responses**: `200 OK` with updated transaction JSON, `400 Bad Request` on invalid fields, or `404 Not Found`.

### `4. DELETE /api/transactions/<int:id>`
Deletes a transaction by ID.
- **Responses**: `200 OK` with `{"message": "Transaction 14 deleted successfully.", "deleted_id": 14}`, or `404 Not Found`.

### `5. GET /api/summary`
Executes SQL-level `SUM(amount)` and `GROUP BY category` aggregation.
- **Response (`200 OK`)**:
```json
{
  "total_spent": 42450.0,
  "total_income": 97500.0,
  "monthly_budget": 50000.0,
  "remaining_budget": 7550.0,
  "budget_utilization_percent": 84.9,
  "budget_alert": true,
  "category_breakdown": [
    { "category": "Housing & Rent", "total": 14500.0 },
    { "category": "Software", "total": 10390.0 }
  ]
}
```

### `6. PUT /api/budget`
Updates the user's monthly budget cap (`monthly_budget > 0`).
- **Request Body**:
```json
{
  "monthly_budget": 60000.0
}
```
- **Responses**: `200 OK` or `400 Bad Request`.
