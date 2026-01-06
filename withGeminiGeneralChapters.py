import os
import requests
import json
import fitz  # PyMuPDF
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# IMPORTANT: Leave the API key as an empty string. The environment will provide it.
API_KEY = "AIzaSyDQU6A8ovEJAMsBR1dMfNephqVobois-rc"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}"
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
                response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                break # Exit loop on success
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 and retries < max_retries - 1:
                    wait_time = 2 ** retries
                    print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
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
                print(f"No text content found in API response for {filename}.")
                return None
        else:
            print(f"No candidates found in API response for {filename}.")
            return None
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error generating HTML for {filename}: {e}")
        print(f"Response content: {response.content.decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error generating HTML for {filename}: {e}")
        return None

def process_monograph(pdf_path, output_dir):
    """
    Processes a single PDF monograph: extracts text, generates HTML, and saves the file.
    """
    filename = os.path.basename(pdf_path)
    print(f"Processing file: {filename}")
    
    pdf_text = get_text_from_pdf(pdf_path)
    if not pdf_text:
        return f"Failed to extract text from {filename}"

    html_content = generate_html_content(pdf_text, filename)
    
    if html_content:
        # Use the original filename with .html extension as requested
        file_without_ext = os.path.splitext(filename)[0]
        output_filename = f"{file_without_ext}.html"
            
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully created: {output_path}")
            return f"Successfully created: {output_path}"
        except Exception as e:
            return f"Failed to write file {output_path}: {e}"
    else:
        return f"Failed to generate HTML for {filename}"

def main():
    """
    Main function to orchestrate the processing of all PDF monographs.
    """
    # Use the specified directory for both input and output
    base_dir = "/Users/fsfatemi/Pharmacopeia/usp44_monographs/General chapters"
    pdfs_dir = base_dir
    output_dir = base_dir

    os.makedirs(pdfs_dir, exist_ok=True)
    
    # Filter for PDF files with numeric names and check for existing HTML
    pdf_files = []
    for f in os.listdir(pdfs_dir):
        file_path = os.path.join(pdfs_dir, f)
        if f.endswith('.pdf') and re.match(r'^[\d.]+$', os.path.splitext(f)[0]):
            output_html_path = os.path.join(output_dir, f"{os.path.splitext(f)[0]}.html")
            if os.path.exists(output_html_path):
                print(f"Skipping '{f}': Corresponding HTML file already exists.")
            else:
                pdf_files.append(file_path)
    
    if not pdf_files:
        print(f"No new numeric PDF files to process in the '{pdfs_dir}' directory. Exiting.")
        return

    results = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(process_monograph, pdf_file, output_dir): pdf_file for pdf_file in pdf_files}
        for future in as_completed(futures):
            pdf_file = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                results.append(f"Processing of {pdf_file} failed with error: {e}")

    print("\n--- Processing Summary ---")
    for result in results:
        print(result)

if __name__ == "__main__":
    main()
