# Harsha's Career Compass - Backend Server (Google Gemini API Version)
# File: app.py

import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, Response
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO

# Initialize the Flask application
app = Flask(__name__, template_folder='templates')

# --- Helper Functions ---

def generate_ai_plan(goal, skill_level, skills_to_learn, hours_per_week):
    """
    Constructs a prompt and sends it to the Gemini API to get a learning plan.
    """
    # --- FIX for Vercel: Configure the API key right when it's needed ---
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not found or is empty.")
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"Error configuring Gemini API key: {e}")
        return None

    # A detailed prompt for the AI to generate a structured plan
    prompt = f"""
    You are an expert career development coach. Your task is to generate a response containing ONLY a valid JSON object. Do not include markdown formatting like ```json or any text before or after the JSON object.

    The JSON object must have a single root key "weekly_plan". This key must contain an array of 8 objects, where each object represents a week.
    Each weekly object must have the following keys: "week", "topic", "details" (as a list of strings), and "resources" (as a list of strings).

    Create this JSON for a user with the following details:
    - Goal: "{goal}"
    - Skill Level: {skill_level}
    - Skills to Learn: {skills_to_learn}
    - Weekly Time: {hours_per_week} hours
    """
    
    try:
        # Using a reliable and fast model from Gemini
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # We configure the model to output JSON directly
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        
        print("--- Sending Prompt to Gemini ---")
        response = model.generate_content(prompt, generation_config=generation_config)
        print("--- Received Response from Gemini ---")

        # The response text should be a clean JSON string
        plan_data = json.loads(response.text)
        
        return plan_data

    except Exception as e:
        print(f"An error occurred while calling the Gemini API: {e}")
        # This will print more detailed errors if the API call fails
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"Gemini API response details: {response.prompt_feedback}")
        return None


def create_pdf(plan_data):
    """
    Generates a PDF document from the learning plan data using ReportLab.
    (This function remains the same)
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
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesoke),
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
        # This error message is shown if the plan generation fails for any reason.
        return jsonify({"error": "Failed to generate plan from AI. Check the server logs for the specific error from the API."}), 500

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
    print("Access at [http://127.0.0.1:5000](http://127.0.0.1:5000)")
    app.run(debug=True, port=5000)

