# Import library dependencies.
from flask import Flask, render_template_string, request, redirect, url_for
import logging
from logging.handlers import RotatingFileHandler
import openai
# Logging Format.
logging_format = logging.Formatter('%(asctime)s %(message)s')

# When testing make sure the key is correct and if it doesn't work make a new one just to be sure
client = openai.OpenAI(api_key = "")

# HTTP Logger.
funnel_logger = logging.getLogger('HTTPLogger')
funnel_logger.setLevel(logging.INFO)
funnel_handler = RotatingFileHandler('http_audits.log', maxBytes=2000, backupCount=5)
funnel_handler.setFormatter(logging_format)
funnel_logger.addHandler(funnel_handler)

app = Flask(__name__)

# AI-Generated Fake Admin Pages using GPT-4o
def generate_deceptive_page():
    prompt = """
    Generate a realistic yet deceptive WordPress admin login page.
    - Must look professional but subtly altered to confuse attackers.
    - Randomly modify form fields, button labels, and page structure.
    - Use inline CSS styles for uniqueness.
    - Do NOT include any real login functionality.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content

@app.route('/')
def index():
    deceptive_html = generate_deceptive_page()
    return render_template_string(deceptive_html)

@app.route('/wp-admin-login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    ip_address = request.remote_addr

    # Log attack attempt
    funnel_logger.info(f'ATTEMPT: IP {ip_address} | Username: {username} | Password: {password}')

    return "Access Denied."

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")