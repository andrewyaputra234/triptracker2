import os
import csv
import pycountry
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

TRIP_FOLDER = "trips"

trips_bp = Blueprint("trips", __name__)


@trips_bp.route("/")
def home():
    sort_order = request.args.get("sort", "desc")

    trips_data = []

    for f in os.listdir(TRIP_FOLDER):
        if f.endswith(".csv"):
            trip_name = f[:-4]
            total = 0.0
            budget = None
            try:
                with open(os.path.join(TRIP_FOLDER, f), "r") as file:
                    reader = csv.reader(file)
                    first_line = next(reader)
                    if first_line[0] == "Budget":
                        budget = float(first_line[1])
                        next(reader)
                    else:
                        file.seek(0)
                        reader = csv.reader(file)
                        next(reader)

                    for row in reader:
                        if len(row) == 4:
                            total += float(row[3])
            except Exception as e:
                print(f"Error reading {f}: {e}")
                continue

            remaining = budget - total if budget is not None else None

            trips_data.append({
                "name": trip_name,
                "total": total,
                "budget": budget,
                "remaining": remaining
            })

    trips_data.sort(key=lambda x: x["total"], reverse=(sort_order != "asc"))

    return render_template("home.html", trips=trips_data, sort_order=sort_order)


import pycountry

@trips_bp.route("/create_trip", methods=["GET", "POST"])
def create_trip():
    countries = {country.alpha_2: country.name for country in pycountry.countries}

    if request.method == "POST":
        country = request.form.get("country", "").strip()
        trip_name = request.form.get("trip_name", "").strip()
        budget = request.form.get("budget", "").strip()

        if not trip_name or not budget or not country:
            flash("Country, trip name and budget cannot be empty.", "danger")
            return redirect(url_for("trips.create_trip"))

        try:
            initial_budget = float(budget)
            if initial_budget <= 0:
                raise ValueError
        except ValueError:
            flash("Budget must be a valid number greater than 0.", "danger")
            return redirect(url_for("trips.create_trip"))

        # Combine country code and trip name to create filename
        full_trip_name = f"{country}_{trip_name}".lower().replace(" ", "_")
        filename = os.path.join(TRIP_FOLDER, f"{full_trip_name}.csv")

        if os.path.exists(filename):
            flash("Trip already exists.", "warning")
            return redirect(url_for("trips.create_trip"))

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Budget", initial_budget])
            writer.writerow(["Date", "Category", "Description", "Amount"])

        flash(f"Trip '{country} {trip_name}' created successfully with budget ${initial_budget}!", "success")
        return redirect(url_for("trips.home"))

    return render_template("create_trip.html", countries=countries)



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
        first_line = next(reader)
        if first_line[0] == "Budget":
            budget = float(first_line[1])
            next(reader)
        else:
            budget = None
            f.seek(0)
            reader = csv.reader(f)
            next(reader)

        for row in reader:
            date, category, description, amount = row
            amount = float(amount)
            expenses.append({"date": date, "category": category, "description": description, "amount": amount})
            total += amount
            category_totals[category] += amount

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
            amount_val = float(amount)
            if amount_val <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid date or amount.", "danger")
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

        if index + 2 >= len(rows):  # Skip 2 header lines
            flash("Invalid expense index.", "danger")
            return redirect(url_for("trips.view_trip", trip_name=trip_name))

        removed = rows.pop(index + 2)

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
    flash(f"Trip '{trip_name}' has been deleted.", "success")
    return redirect(url_for("trips.home"))


@trips_bp.route("/ai_recommendation/<trip_name>")
def ai_recommendation(trip_name):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    if not os.path.exists(filename):
        flash("Trip not found.", "danger")
        return redirect(url_for("trips.home"))

    budget = None
    total = 0.0
    expenses_text = ""

    with open(filename, "r") as f:
        reader = csv.reader(f)
        first_line = next(reader)
        if first_line[0] == "Budget":
            budget = float(first_line[1])
            next(reader)
        else:
            f.seek(0)
            reader = csv.reader(f)
            next(reader)

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
    except Exception:
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
    
@trips_bp.route("/trip/<trip_name>/update_budget", methods=["POST"])
def update_budget(trip_name):
    new_budget_str = request.form.get("new_budget", "").strip()
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")

    if not os.path.exists(filename):
        flash("Trip file not found.", "danger")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    try:
        new_budget = float(new_budget_str)
        if new_budget <= 0:
            flash("Budget must be greater than 0.", "danger")
            return redirect(url_for("trips.view_trip", trip_name=trip_name))
    except ValueError:
        flash("Invalid budget value.", "danger")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    try:
        with open(filename, "r") as f:
            rows = list(csv.reader(f))

        if rows[0][0] == "Budget":
            rows[0][1] = str(new_budget)
        else:
            # If no budget line, insert one at the top
            rows.insert(0, ["Budget", str(new_budget)])

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        flash("Budget updated successfully!", "success")
    except Exception as e:
        flash(f"Error updating budget: {str(e)}", "danger")

    return redirect(url_for("trips.view_trip", trip_name=trip_name))
