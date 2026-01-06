# PDF to Farsi Translator Web Application

A Flask web application that translates USP Monograph PDF files to Farsi HTML documents using Google's Gemini AI.

## Features

- 📤 **Easy PDF Upload**: Drag-and-drop or click to upload PDF files
- 🌐 **Web Interface**: Clean, modern, and user-friendly interface
- 🔄 **Real-time Processing**: Progress indicators during translation
- ⬇️ **Instant Download**: Download translated HTML files immediately
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /Users/fsfatemi/Translate_chat_bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the web application**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Upload and translate**:
   - Click the upload area or drag-and-drop a PDF file
   - Click "Translate PDF" button
   - Wait for processing (may take a few moments)
   - Download the translated HTML file

## How It Works

1. User uploads a USP Monograph PDF file through the web interface
2. The application extracts text from the PDF using PyMuPDF
3. Text is sent to Google's Gemini AI for translation to Farsi
4. AI generates a formatted HTML document with:
   - Right-to-left (RTL) layout for Farsi text
   - Proper styling with Tailwind CSS
   - Vazirmatn font for Farsi content
   - MathJax for mathematical formulas
   - Preserved technical terms and units in English
5. User downloads the generated HTML file

## File Structure

```
Translate_chat_bot/
├── app.py                              # Flask web application
├── withGeminiGeneralChapters.py        # Original batch processing script
├── requirements.txt                     # Python dependencies
├── templates/
│   └── index.html                      # Web interface template
└── README.md                           # This file
```

## API Key Configuration

The application uses Google's Gemini API. The API key is currently hardcoded in both `app.py` and `withGeminiGeneralChapters.py`. For production use, consider:

- Setting the API key as an environment variable
- Using a configuration file
- Implementing proper security measures

## Limitations

- Maximum file size: 16MB
- Supports PDF files only
- Requires active internet connection for API calls
- Rate limiting may apply based on API usage

## Technical Details

### Dependencies
- **Flask**: Web framework
- **PyMuPDF (fitz)**: PDF text extraction
- **Requests**: HTTP requests to Gemini API
- **Werkzeug**: Secure filename handling

### Translation Features
- Translates descriptive text to Farsi
- Preserves units (ml, mg, nm, etc.) in English
- Maintains chemical formulas and scientific notations
- Converts general chapter references to hyperlinks
- Formats tables with proper RTL alignment
- Includes MathJax for LaTeX formulas

## Troubleshooting

**Port already in use:**
```bash
# Change the port in app.py or kill the process using port 5000
lsof -ti:5000 | xargs kill -9
```

**File upload fails:**
- Check file size (must be < 16MB)
- Ensure file is a valid PDF
- Check API key is valid

**Translation errors:**
- Verify internet connection
- Check API rate limits
- Review console logs for detailed error messages

## License

This project is for educational and internal use.
