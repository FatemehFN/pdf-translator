import os
import tempfile
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from functools import wraps
import fitz  # PyMuPDF
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Login credentials - Change these or set via environment variables
USERNAME = os.environ.get('APP_USERNAME', 'admin')
PASSWORD = os.environ.get('APP_PASSWORD', 'password123')

# Get port from environment variable for deployment
PORT = int(os.environ.get('PORT', 5000))

ALLOWED_EXTENSIONS = {'pdf'}

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Get API key from environment variable (REQUIRED - set in Render dashboard)
API_KEY = os.environ.get('GEMINI_API_KEY')
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required but not set")
# Use the v1 API endpoint with correct model name
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}"

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def too_large(e):
    """Handle file too large errors."""
    return jsonify({'error': 'File is too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all other exceptions."""
    print(f"Unhandled exception: {e}")
    return jsonify({'error': f'An error occurred: {str(e)}'}), 500

def get_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file using PyMuPDF.
    """
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def generate_html_content(pdf_text, filename):
    """
    Generates Farsi HTML from the extracted English text using the Gemini API.
    This function uses a prompt to guide the model on the desired structure.
    """
    prompt = f"""
You are an expert at converting English USP Monograph PDF text into a single, self-contained Farsi HTML document. Your task is to generate a complete HTML file that strictly adheres to the following blueprint.

**1. Overall HTML Structure**
* The document must be a standard HTML5 file.
* Use `lang="fa"` and `dir="rtl"` in the `<html>` tag.
* The `<head>` section must include `<meta charset="UTF-8">`, a viewport meta tag, and the `<title>` translated to Farsi.
* All content must be wrapped in a `div` with the class `container mx-auto p-4 max-w-4xl`.
* The content should be a single, flowing document without any tabs or interactive elements.

**2. External Dependencies**
* **CSS:** Load Tailwind CSS from the CDN: `<script src="https://cdn.tailwindcss.com"></script>`.
* **Font:** Load the `Vazirmatn` font from Google Fonts: `<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap" rel="stylesheet">`.
* **MathJax:** Include the standard MathJax CDN script for LaTeX rendering.
* **JS Libraries:** Do not include any libraries for downloading or saving content.

**3. Internal Styling (`<style>` Block)**
The HTML file must contain a `<style>` block with the following exact CSS rules:
* `body`: `font-family: 'Vazirmatn', sans-serif;`, `background-color: #f8fafc;`, `color: #333;`.
* `.card`: `background-color: #fff;`, `border-radius: 0.5rem;`, `padding: 1.5rem;`, `box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);`.
* `.ltr-text`: `direction: ltr;`, `text-align: left;`, `display: inline-block;`.
* `table`: `width: 100%;`, `margin-left: auto;`, `margin-right: auto;`, `direction: rtl;`, `text-align: center;`, `border-collapse: collapse;`, `margin-top: 1rem;`, `margin-bottom: 1rem;`.
* `table th, table td`: `border: 1px solid #e2e8f0;`, `padding: 0.75rem;`, `text-align: center;`.
* `table th`: `background-color: #f1f5f9;`, `font-weight: bold;`.
* `.formula-display`: `display: flex;`, `justify-content: center;`, `margin-top: 1rem;`, `margin-bottom: 1rem;`, `direction: ltr;`.

**4. Headers and Titles**
* The main title (`<h1>`) must use the exact classes `text-3xl font-bold text-center text-blue-700 mb-6`.
* Section titles (`<h2>`) must use `text-2xl font-semibold text-blue-600 mb-4`.
* Sub-section titles (`<h3>`) must use `text-xl font-semibold text-blue-600 mb-2`.
* Procedure titles (`<h4>`) must use `text-lg font-semibold text-gray-700 mt-3 mb-2`.

**5. Content Formatting**
* Translate all descriptive text and tables into Farsi. Do not translate any formulas, or units.
* Do not translate units. For instance, ml, mg, nm, etc., should remain in English.
* Translate the word "anhydrous" to انیدروس.
* All numbers, units, chemical formulas, and scientific notations (e.g., `1-cm`, `200 to 400 nm`, `3800 to 650 cm-¹`) must be wrapped in `<span class="ltr-text">` tags.
* All mathematical formulas must be in LaTeX format and displayed within a `div` with the class `formula-display`. The formulas themselves must be in English.
* All references to general chapters (e.g., `854`) must be hyperlinks. The link text must be only the number, and the `href` attribute must point to a local path (e.g., `<a href="854.html" class="text-blue-600 hover:underline" target="_blank">854</a>`).
* All table content, including headers and cell data, must be translated into Farsi. Tables should be horizontally centered on the page.

**6. Interactive Elements**
* **You must not create any interactive elements such as input fields, dropdown menus, or textareas.**
* **You must not create any download buttons or related functionality.**

**Source Text for Conversion:**

Here is the text from the PDF file for the monograph titled "{filename}":

{pdf_text}"""

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "tools": []  # Setting 'tools' to an empty list disables all tools, including Google Search (Grounding)
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"Generating HTML for {filename}...")
        retries = 0
        max_retries = 5
        while retries < max_retries:
            try:
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=120)
                response.raise_for_status()
                break  # Exit loop on success
            except requests.exceptions.HTTPError as e:
                # Retry on rate limit (429) or service unavailable (503)
                if e.response.status_code in [429, 503] and retries < max_retries - 1:
                    wait_time = 2 ** retries
                    error_name = "Rate limit exceeded" if e.response.status_code == 429 else "Service unavailable"
                    print(f"{error_name}. Retrying in {wait_time} seconds... (attempt {retries + 1}/{max_retries})")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"HTTP Error: {e}")
                    print(f"Response: {e.response.content.decode('utf-8') if e.response else 'No response'}")
                    raise e
        
        candidates = response.json().get('candidates', [])
        if candidates:
            part = candidates[0].get('content', {}).get('parts', [])[0]
            generated_text = part.get('text')
            
            if generated_text:
                if generated_text.startswith("```html") and generated_text.endswith("```"):
                    generated_text = generated_text[len("```html"):].strip()
                    generated_text = generated_text[:-len("```")].strip()
                return generated_text
            else:
                error_msg = f"No text content found in API response for {filename}."
                print(error_msg)
                return None
        else:
            error_msg = f"No candidates found in API response. Response: {response.json()}"
            print(error_msg)
            return None
    except requests.exceptions.Timeout:
        print(f"Timeout error generating HTML for {filename}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error generating HTML for {filename}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response content: {e.response.content.decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error generating HTML for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Render the main page with the upload form."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle PDF upload and translation."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload a PDF file.'}), 400
    
    try:
        # Save the uploaded file temporarily
        filename = secure_filename(file.filename)
        temp_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_pdf_path)
        
        # Extract text from PDF
        pdf_text = get_text_from_pdf(temp_pdf_path)
        if not pdf_text:
            os.remove(temp_pdf_path)
            return jsonify({'error': 'Failed to extract text from PDF'}), 500
        
        # Generate HTML content
        html_content = generate_html_content(pdf_text, filename)
        
        # Clean up temporary PDF
        os.remove(temp_pdf_path)
        
        if not html_content:
            return jsonify({'error': 'Failed to generate translated HTML'}), 500
        
        # Save HTML to temporary file
        html_filename = os.path.splitext(filename)[0] + '.html'
        temp_html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)
        
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{html_filename}'
        })
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download the translated HTML file."""
    try:
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))
        
        if not os.path.exists(temp_path):
            return jsonify({'error': 'File not found'}), 404
        
        response = send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
        
        # Schedule file deletion after download
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Error cleaning up file: {e}")
        
        return response
        
    except Exception as e:
        print(f"Error downloading file: {e}")
        return jsonify({'error': 'Error downloading file'}), 500

if __name__ == '__main__':
    # Use environment variables for production deployment
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
