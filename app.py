from datetime import date
import heapq
import sqlite3
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "blood-bank-project-key"
DATABASE = "blood_bank.db"

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS blood_units (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_code TEXT NOT NULL UNIQUE,
                blood_group TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_inventory():
    with get_db() as db:
        return db.execute("""
            SELECT * FROM blood_units
            ORDER BY expiry_date ASC, id ASC
        """).fetchall()


def available_units_for_group(blood_group):
    today = date.today().isoformat()
    with get_db() as db:
        return db.execute("""
            SELECT * FROM blood_units
            WHERE blood_group = ? AND status = 'Available' AND expiry_date >= ?
            ORDER BY expiry_date ASC, id ASC
        """, (blood_group, today)).fetchall()


def choose_earliest_expiring_unit(units):
    """Use a min-heap to choose the eligible unit with the earliest expiry date."""
    priority_queue = []
    for unit in units:
        heapq.heappush(
            priority_queue,
            (unit["expiry_date"], unit["id"], unit["unit_code"])
        )
    if not priority_queue:
        return None
    return heapq.heappop(priority_queue)


@app.route("/")
def dashboard():
    today = date.today().isoformat()
    with get_db() as db:
        total_available = db.execute(
            "SELECT COUNT(*) FROM blood_units WHERE status = 'Available' AND expiry_date >= ?",
            (today,)
        ).fetchone()[0]
        expired_available = db.execute(
            "SELECT COUNT(*) FROM blood_units WHERE status = 'Available' AND expiry_date < ?",
            (today,)
        ).fetchone()[0]
        group_rows = db.execute("""
            SELECT blood_group, COUNT(*) AS quantity
            FROM blood_units
            WHERE status = 'Available' AND expiry_date >= ?
            GROUP BY blood_group
            ORDER BY blood_group
        """, (today,)).fetchall()
    return render_template(
        "index.html",
        total_available=total_available,
        expired_available=expired_available,
        group_rows=group_rows,
        today=today
    )


@app.route("/add", methods=["GET", "POST"])
def add_unit():
    if request.method == "POST":
        unit_code = request.form.get("unit_code", "").strip()
        blood_group = request.form.get("blood_group", "")
        expiry_date = request.form.get("expiry_date", "")

        if not unit_code or blood_group not in BLOOD_GROUPS or not expiry_date:
            flash("Please complete all fields correctly.", "error")
            return redirect(url_for("add_unit"))

        try:
            date.fromisoformat(expiry_date)
        except ValueError:
            flash("Please enter a valid expiry date.", "error")
            return redirect(url_for("add_unit"))

        if expiry_date < date.today().isoformat():
            flash("Expiry date cannot be in the past.", "error")
            return redirect(url_for("add_unit"))

        try:
            with get_db() as db:
                db.execute(
                    "INSERT INTO blood_units (unit_code, blood_group, expiry_date) VALUES (?, ?, ?)",
                    (unit_code, blood_group, expiry_date)
                )
            flash("Blood unit added successfully.", "success")
            return redirect(url_for("inventory"))
        except sqlite3.IntegrityError:
            flash("That unit ID already exists. Please use a unique ID.", "error")
            return redirect(url_for("add_unit"))

    return render_template("add_unit.html", blood_groups=BLOOD_GROUPS, today=date.today().isoformat())


@app.route("/inventory")
def inventory():
    units = get_inventory()
    today = date.today().isoformat()
    return render_template("inventory.html", units=units, today=today)


@app.route("/issue", methods=["GET", "POST"])
def issue_blood():
    result = None
    selected_group = ""
    if request.method == "POST":
        selected_group = request.form.get("blood_group", "")
        if selected_group not in BLOOD_GROUPS:
            flash("Please select a valid blood group.", "error")
            return redirect(url_for("issue_blood"))

        units = available_units_for_group(selected_group)
        chosen = choose_earliest_expiring_unit(units)

        if chosen is None:
            flash(f"No available, unexpired units found for {selected_group}.", "error")
        else:
            unit_id = chosen[1]
            with get_db() as db:
                db.execute(
                    "UPDATE blood_units SET status = 'Issued' WHERE id = ? AND status = 'Available'",
                    (unit_id,)
                )
                result = db.execute(
                    "SELECT * FROM blood_units WHERE id = ?", (unit_id,)
                ).fetchone()
            flash(f"Unit {result['unit_code']} issued successfully.", "success")

    return render_template(
        "issue_blood.html",
        blood_groups=BLOOD_GROUPS,
        selected_group=selected_group,
        result=result
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
