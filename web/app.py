from flask import Flask
from routes.trips import trips_bp
from routes.budgets import budgets_bp
from routes.charts import charts_bp
from dotenv import load_dotenv
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.secret_key = "String_23"  # replace with a secure key in production

# Register Blueprints (your separated route modules)
app.register_blueprint(trips_bp)
app.register_blueprint(budgets_bp)
app.register_blueprint(charts_bp)

if __name__ == "__main__":
    app.run(debug=True)
