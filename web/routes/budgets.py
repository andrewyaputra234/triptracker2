from flask import Blueprint, render_template, request, redirect, url_for, flash
from utils.csv_helpers import load_budgets, save_budgets

budgets_bp = Blueprint("budgets", __name__)

@budgets_bp.route("/trip/<trip_name>/set_budget", methods=["GET", "POST"])
def set_budget(trip_name):
    budgets = load_budgets()
    current_budget = budgets.get(trip_name, 0)

    if request.method == "POST":
        try:
            new_budget = float(request.form["budget"])
            if new_budget <= 0:
                raise ValueError("Budget must be positive.")
            budgets[trip_name] = new_budget
            save_budgets(budgets)
            flash("Budget updated!", "success")
            return redirect(url_for("trips.view_trip", trip_name=trip_name))
        except ValueError:
            flash("Please enter a valid budget.", "danger")

    return render_template("set_budget.html", trip_name=trip_name, current_budget=current_budget)
