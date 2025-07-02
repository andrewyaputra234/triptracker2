import csv
import os

BUDGET_FILE = os.path.join("trips", "budgets.csv")

def load_budgets():
    budgets = {}
    if os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    budgets[row[0]] = float(row[1])
    return budgets

def save_budgets(budgets):
    with open(BUDGET_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for trip, budget in budgets.items():
            writer.writerow([trip, budget])
