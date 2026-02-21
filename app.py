import os
import tempfile
import time
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
from functools import wraps
import fitz  # PyMuPDF
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# LOAD ENV
# =========================
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

USERNAME = os.environ.get('APP_USERNAME', 'admin')
PASSWORD = os.environ.get('APP_PASSWORD', 'password123')

# =========================
# GAPGPT CLIENT
# =========================
client = OpenAI(
    api_key=os.environ.get("GAPGPT_API_KEY"),
    base_url="https://api.gapgpt.app/v1"
)

ALLOWED_EXTENSIONS = {'pdf'}


# =========================
# AUTH DECORATOR
# =========================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# =========================
# PDF TEXT EXTRACTION
# =========================
def get_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return None


# =========================
# TEXT CHUNKING
# =========================
def chunk_text(text, max_chars=6000, overlap=800):
    if not text:
        return []

    length = len(text)
    if length <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < length:
        end = min(start + max_chars, length)
        chunks.append(text[start:end])

        if end >= length:
            break

        start = max(0, end - overlap)

    return chunks


# =========================
# GEMINI GENERATION (Chunked + Retry)
# =========================
def generate_html_content(pdf_text, filename):

    chunks = chunk_text(pdf_text)
    total_parts = len(chunks)
    print(f"{filename} split into {total_parts} chunk(s)")

    all_fragments = []

    for index, chunk in enumerate(chunks):
        part_number = index + 1

        prompt = f"""
You are an expert at converting English USP Monograph PDF text into a complete Farsi HTML document.

IMPORTANT:
- Output ONLY inner HTML for this chunk.
- No <html>, <head>, <body>.
- No interactive elements.
- Translate descriptive text to Farsi.
- Do NOT translate units or formulas.
- Wrap numbers/units in <span class="ltr-text">.

PART {part_number}/{total_parts}

{chunk}
"""

        retries = 0
        max_retries = 5

        while retries < max_retries:
            try:
                print(f"Generating part {part_number}/{total_parts}...")

                response = client.chat.completions.create(
                    model="gemini-2.5-flash",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )

                generated_text = response.choices[0].message.content
                break

            except Exception as e:
                wait_time = 2 ** retries
                print(f"Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                retries += 1

                if retries == max_retries:
                    print("Max retries reached.")
                    return None

        if generated_text.startswith("```"):
            generated_text = generated_text.strip("`").replace("html", "").strip()

        all_fragments.append(generated_text)

    combined_inner_html = "\n\n".join(all_fragments)

    # Wrap final document once
    return build_full_html_document(combined_inner_html, filename)


# =========================
# FULL HTML WRAPPER
# =========================
def build_full_html_document(inner_html, filename):
    title = os.path.splitext(filename)[0]

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap" rel="stylesheet">
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
body {{
    font-family: 'Vazirmatn', sans-serif;
    background-color: #f8fafc;
    color: #333;
}}
.card {{
    background-color: #fff;
    border-radius: 0.5rem;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}}
.ltr-text {{
    direction: ltr;
    text-align: left;
    display: inline-block;
}}
table {{
    width: 100%;
    direction: rtl;
    text-align: center;
    border-collapse: collapse;
    margin: 1rem 0;
}}
table th, table td {{
    border: 1px solid #e2e8f0;
    padding: 0.75rem;
}}
table th {{
    background-color: #f1f5f9;
    font-weight: bold;
}}
.formula-display {{
    display: flex;
    justify-content: center;
    margin: 1rem 0;
    direction: ltr;
}}
</style>
</head>
<body>
<div class="container mx-auto p-4 max-w-4xl">
{inner_html}
</div>
</body>
</html>
"""


# =========================
# ROUTES
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == USERNAME and request.form.get('password') == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        filename = secure_filename(file.filename)
        temp_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_pdf_path)

        pdf_text = get_text_from_pdf(temp_pdf_path)
        os.remove(temp_pdf_path)

        if not pdf_text:
            return jsonify({'error': 'PDF extraction failed'}), 500

        html_content = generate_html_content(pdf_text, filename)

        if not html_content:
            return jsonify({'error': 'Translation failed'}), 500

        html_filename = os.path.splitext(filename)[0] + '.html'
        temp_html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_filename)

        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return jsonify({
            'success': True,
            'download_url': f'/download/{html_filename}'
        })

    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
@login_required
def download_file(filename):
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))

    if not os.path.exists(temp_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(temp_path, as_attachment=True)


# =========================
# RUN
# =========================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)