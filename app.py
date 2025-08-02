# Harsha's Career Compass - Backend Server (Perplexity API Version)
# File: app.py

import os
import json
import requests
from flask import Flask, request, jsonify, render_template, Response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# Initialize the Flask application
app = Flask(__name__, template_folder='templates')

# --- Configuration ---
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
# The API key will be read from an environment variable for security
API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# --- Helper Functions ---

def generate_ai_plan(goal, skill_level, skills_to_learn, hours_per_week):
    """
    Constructs a prompt and sends it to the Perplexity API to get a learning plan.
    """
    if not API_KEY:
        print("Error: PERPLEXITY_API_KEY environment variable not set.")
        return None

    # A detailed prompt for the AI to generate a structured plan
    system_prompt = """
    You are an expert career development coach. You always generate a response in a structured JSON format. The JSON object must have a single key "weekly_plan". The "weekly_plan" value should be an array of 8 objects, where each object represents a week. Each weekly object must have the following keys: "week", "topic", "details" (as a list of strings), and "resources" (as a list of strings). Do not include any introductory text or explanations outside of the JSON object itself.
    """
    
    user_prompt = f"""
    Create a detailed, structured, 8-week learning plan for a user with the following details:
    - User's Goal: Become a "{goal}"
    - Current Skill Level: {skill_level}
    - Specific Skills to Learn: {skills_to_learn}
    - Available Study Time: {hours_per_week} hours per week
    """

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3-sonar-large-32k-online", # A powerful model from Perplexity
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60) # 60-second timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        
        response_data = response.json()
        # The AI's response is a JSON string inside the content field
        content_string = response_data['choices'][0]['message']['content']
        plan_data = json.loads(content_string)
        
        return plan_data

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Perplexity API: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error processing response from Perplexity: {e}")
        print(f"Received data: {response.text}")
        return None


def create_pdf(plan_data):
    """
    Generates a PDF document from the learning plan data using ReportLab.
    (This function remains the same as before)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = []
    title = Paragraph("Your Personalized Career Compass Plan", styles['h1'])
    story.append(title)
    story.append(Spacer(1, 24))
    intro_text = f"Here is your 8-week learning plan to achieve your goal. Stick to the schedule, and you'll make great progress!"
    story.append(Paragraph(intro_text, styles['BodyText']))
    story.append(Spacer(1, 24))
    for week_plan in plan_data.get('weekly_plan', []):
        week_title = Paragraph(f"<b>{week_plan['week']}: {week_plan['topic']}</b>", styles['h3'])
        story.append(week_title)
        story.append(Spacer(1, 12))
        details_list = [Paragraph(f"• {item}", styles['BodyText']) for item in week_plan['details']]
        resources_list = [Paragraph(f"• {item}", styles['BodyText']) for item in week_plan['resources']]
        table_data = [
            [Paragraph("<b>Details</b>", styles['Normal']), Paragraph("<b>Suggested Resources</b>", styles['Normal'])],
            [details_list, resources_list]
        ]
        table = Table(table_data, colWidths=[250, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 24))
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Flask Routes ---

@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """API endpoint to generate the learning plan."""
    if not API_KEY:
        return jsonify({"error": "API key is not configured on the server."}), 500
        
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid input"}), 400

    goal = data.get('goal')
    skill_level = data.get('skillLevel')
    skills_to_learn = data.get('skills')
    hours_per_week = data.get('hours')

    if not all([goal, skill_level, skills_to_learn, hours_per_week]):
        return jsonify({"error": "Missing required fields"}), 400

    plan = generate_ai_plan(goal, skill_level, skills_to_learn, hours_per_week)

    if plan and 'weekly_plan' in plan:
        return jsonify(plan)
    else:
        return jsonify({"error": "Failed to generate plan from AI. The API may be down or the response was invalid."}), 500

@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """API endpoint to generate and download the plan as a PDF."""
    plan_data = request.get_json()
    if not plan_data:
        return "Invalid data", 400
    pdf_buffer = create_pdf(plan_data)
    return Response(
        pdf_buffer,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment;filename=Career_Compass_Plan.pdf'}
    )

# This block is for local development only and will be ignored by Vercel/Netlify
if __name__ == '__main__':
    print("Starting Harsha's Career Compass server for local development...")
    print("Access at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
