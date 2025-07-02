from flask import Blueprint, send_file, flash, redirect, url_for, render_template
import csv
import os
import io
import matplotlib.pyplot as plt
from collections import defaultdict

charts_bp = Blueprint("charts", __name__)
TRIP_FOLDER = "trips"

@charts_bp.route("/trip/<trip_name>/chart.png")
def category_chart_image(trip_name):
    filename = os.path.join(TRIP_FOLDER, f"{trip_name}.csv")
    category_totals = defaultdict(float)

    try:
        with open(filename, mode="r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header
            for row in reader:
                _, category, _, amount = row
                category_totals[category] += float(amount)
    except Exception as e:
        flash(f"Error generating chart: {e}", "danger")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    if not category_totals:
        flash("No data to generate chart.", "warning")
        return redirect(url_for("trips.view_trip", trip_name=trip_name))

    # Create bar chart
    fig, ax = plt.subplots()
    ax.bar(category_totals.keys(), category_totals.values(), color='skyblue')
    ax.set_title(f"Spending by Category - {trip_name}")
    ax.set_ylabel("Amount ($)")
    ax.set_xlabel("Category")
    plt.xticks(rotation=45)

    # Save chart to memory buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


@charts_bp.route("/trip/<trip_name>/chart")
def view_chart(trip_name):
    # Render a template that will show the image
    return render_template("charts.html", trip_name=trip_name)
