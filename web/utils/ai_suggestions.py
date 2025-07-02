import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_spending_suggestions(trip_name, total_spent, remaining, category_totals):
    category_summary = "\n".join([f"{cat}: ${amt:.2f}" for cat, amt in category_totals.items()])

    prompt = f"""
Trip Name: {trip_name}
Total Spent: ${total_spent:.2f}
Remaining Budget: ${remaining:.2f}
Category Breakdown:
{category_summary}

Based on the above trip spending, suggest 2-3 smart ways the user could spend the remaining budget wisely. Keep it concise.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or gpt-4 if you have access
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"⚠️ AI suggestion failed: {str(e)}"
