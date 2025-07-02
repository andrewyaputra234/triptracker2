import os
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from collections import defaultdict
from utils.csv_helpers import load_budgets
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # call this once at the start of your app

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

TRIP_FOLDER = "trips"

trips_bp = Blueprint("trips", __name__)

@trips_bp.route("/")
def home():
    sort_order = request.args.get("sort", "desc")  # default descending

    budgets = load_budgets()
    trips_data = []

    for f in os.listdir(TRIP_FOLDER):
        if f.endswith(".csv"):
            trip_name = f[:-4]
            total = 0.0
            try:
                with open(os.path.join(TRIP_FOLDER, f), "r") as file:
                    reader = csv.reader(file)
                    next(reader)
                    for row in reader:
                        if len(row) == 4:
                            total += float(row[3])
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue

            budget = budgets.get(trip_name)
            remaining = budget - total if budget is not None else None

            trips_data.append({
                "name": trip_name,
                "total": total,
                "budget": budget,
                "remaining": remaining
            })

    if sort_order == "asc":
        trips_data.sort(key=lambda x: x["total"])
    else:
        trips_data.sort(key=lambda x: x["total"], reverse=True)

    return render_template("home.html", trips=trips_data, sort_order=sort_order)


@trips_bp.route("/create_trip", methods=["GET", "POST"])
def create_trip():
    if request.method == "POST":
        trip_name = request.form.get("trip_name", "").strip()
        if not trip_name:
            flash("Trip name cannot be empty.", "danger")
            return redirect(url_for("trips.create_trip"))

        filename = os.path.join(TRIP_FOLDER, f"{trip_name.lower()}.csv")
        if os.path.exists(filename):
            flash("Trip already exists.", "warning")
            return redirect(url_for("trips.create_trip"))

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Category", "Description", "Amount"])
        flash(f"Trip '{trip_name}' created successfully!", "success")
        return redirect(url_for("trips.home"))

    return render_template("create_trip.html")


@trips_bp.route("/trip/<trip_name>")
def view_trip(trip_name):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    if not os.path.exists(filename):
        flash("Trip not found.", "danger")
        return redirect(url_for("trips.home"))

    expenses = []
    total = 0.0
    category_totals = defaultdict(float)

    with open(filename, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            date, category, description, amount = row
            amount = float(amount)
            expenses.append({"date": date, "category": category, "description": description, "amount": amount})
            total += amount
            category_totals[category] += amount

    budgets = load_budgets()
    budget = budgets.get(trip_name)
    remaining = budget - total if budget is not None else None

    return render_template("trip.html", trip_name=trip_name, expenses=expenses, total=total,
                           category_totals=category_totals, budget=budget, remaining=remaining)


@trips_bp.route("/trip/<trip_name>/add", methods=["GET", "POST"])
def add_expense(trip_name):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")

    if request.method == "POST":
        date = request.form.get("date", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        amount = request.form.get("amount", "").strip()

        if not date or not category or not description or not amount:
            flash("All fields are required.", "danger")
            return redirect(url_for("trips.add_expense", trip_name=trip_name))

        try:
            from datetime import datetime
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", "danger")
            return redirect(url_for("trips.add_expense", trip_name=trip_name))

        try:
            amount_val = float(amount)
            if amount_val <= 0:
                flash("Amount must be greater than 0.", "danger")
                return redirect(url_for("trips.add_expense", trip_name=trip_name))
        except ValueError:
            flash("Amount must be a number.", "danger")
            return redirect(url_for("trips.add_expense", trip_name=trip_name))

        with open(filename, mode="a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([date, category, description, amount_val])
        flash("Expense added successfully!", "success")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    return render_template("add_expense.html", trip_name=trip_name)


@trips_bp.route("/trip/<trip_name>/delete/<int:index>", methods=["POST"])
def delete_expense(trip_name, index):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    try:
        with open(filename, "r") as f:
            rows = list(csv.reader(f))

        if index + 1 >= len(rows):
            flash("Invalid expense index.", "danger")
            return redirect(url_for("trips.view_trip", trip_name=trip_name))

        removed = rows.pop(index + 1)  # skip header

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        flash(f"Removed expense: {removed[2]} (${removed[3]})", "success")
    except Exception as e:
        flash(f"Error deleting expense: {str(e)}", "danger")

    return redirect(url_for("trips.view_trip", trip_name=trip_name))


@trips_bp.route("/delete_trip/<trip_name>", methods=["POST"])
def delete_trip(trip_name):
    trip_file = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    if os.path.exists(trip_file):
        os.remove(trip_file)

    budgets = load_budgets()
    if trip_name in budgets:
        del budgets[trip_name]
        from utils.csv_helpers import save_budgets
        save_budgets(budgets)

    flash(f"Trip '{trip_name}' has been deleted.", "success")
    return redirect(url_for("trips.home"))


@trips_bp.route("/ai_recommendation/<trip_name>")
def ai_recommendation(trip_name):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    if not os.path.exists(filename):
        flash("Trip not found.", "danger")
        return redirect(url_for("trips.home"))

    budgets = load_budgets()
    budget = budgets.get(trip_name)

    expenses_text = ""
    total = 0.0
    with open(filename, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            if len(row) == 4:
                date, category, description, amount = row
                expenses_text += f"- {date}: {category}, {description}, ${amount}\n"
                total += float(amount)

    if budget is None:
        flash("No budget set for this trip.", "warning")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    remaining = budget - total

    prompt = (
        f"Here are the expenses for my trip '{trip_name}':\n"
        f"{expenses_text}\n"
        f"My total budget is ${budget:.2f} and my remaining budget is ${remaining:.2f}. "
        "Please suggest how I should allocate my remaining budget wisely."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that gives budget advice."},
                {"role": "user", "content": prompt}
            ]
        )
        ai_suggestion = response.choices[0].message.content
    except Exception as e:
        ai_suggestion = "Sorry, the AI service is currently unavailable."

    return render_template("ai_recommendation.html", suggestion=ai_suggestion, trip_name=trip_name)


@trips_bp.route("/api/ai_chat/<trip_name>", methods=["POST"])
def ai_chat(trip_name):
    data = request.get_json()
    messages = data.get("messages")

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        ai_reply = response.choices[0].message.content
        return jsonify({"reply": ai_reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

