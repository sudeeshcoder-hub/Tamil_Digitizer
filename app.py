import os
import json
import re
import mimetypes
from google import genai
from google.genai import types
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from docxtpl import DocxTemplate

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")

# 2. Configure Google Gemini AI Client
# The new SDK uses a Client object instead of genai.configure()
if not API_KEY:
    print("CRITICAL ERROR: No API Key found in .env file!")
    client = None
else:
    client = genai.Client(api_key=API_KEY)

app = Flask(__name__)

# 3. Configure Folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# --- CLEANING HELPER FUNCTIONS ---
def clean_option_text(text):
    if not text:
        return ""
    # Removes labels like 'a)', '1.', 'அ)' from the start
    cleaned = re.sub(r'^\s*\(?[\w\u0B80-\u0BFF]+[\.\)]\s*', '', text)
    return cleaned

def clean_json_data(data):
    if "sections" in data:
        for section in data["sections"]:
            if "questions" in section:
                for q in section["questions"]:
                    if "options" in q and q["options"]:
                        q["options"] = [clean_option_text(opt) for opt in q["options"]]
    
    if "items" in data:
        for item in data["items"]:
            if "options" in item and item["options"]:
                item["options"] = [clean_option_text(opt) for opt in item["options"]]
    return data

# --- AI LOGIC ---
def analyze_image_with_gemini(image_path, mode):
    if client is None:
        return {"error": "API Client not initialized. Check your API Key."}

    # 1. Detect the correct MIME type (e.g., image/png, image/jpeg)
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg" # Default fallback

    print(f"Processing file: {image_path} | Detected Type: {mime_type}")

    model_id = 'gemini-3-flash-preview'

    base_instruction = """
    You are an expert Tamil Data Entry Operator.
    Analyze this image. Extract content into valid JSON.
    Do NOT use Markdown. Return raw JSON only.
    Preserve Tamil script exactly.
    """

    if mode == "mak-tamil":
        specific_instruction = """
        TASK: Extract structured Tamil Question Paper for 'MAK Group of Schools'.
        JSON OUTPUT FORMAT:
        {
          "header": { "class": "...", "marks": "...", "date": "...", "time": "..." },
          "sections": [
            {
              "roman": "I",
              "title": "Section Title",
              "marks_eq": "6 X 1 = 6",
              "questions": [
                { "no": "1", "text": "Question text...", "type": "mcq", "options": ["Opt1", "Opt2"] }
              ]
            }
          ]
        }
        """
    elif mode == "original":
        specific_instruction = """
        TASK: Extract content EXACTLY as seen in the image.
        JSON OUTPUT FORMAT:
        { "items": [ { "type": "original", "content": "Text...", "style": "text" } ] }
        """
    elif mode == "choose":
        specific_instruction = """
        TASK: Extract ONLY Multiple Choice Questions (MCQs).
        JSON: { "items": [ { "type": "mcq", "q_no": "1", "text": "...", "options": [...] } ] }
        """
    elif mode == "paragraph":
        specific_instruction = """
        TASK: Extract ONLY Paragraphs.
        JSON: { "items": [ { "type": "para", "heading": "...", "text": "..." } ] }
        """
    else: 
        specific_instruction = """
        TASK: Extract EVERYTHING.
        JSON: { "items": [ { "type": "mcq", "text": "...", "options": [...] }, { "type": "para", "text": "..." } ] }
        """

    final_prompt = base_instruction + specific_instruction

    try:
        # Read the file bytes
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Send to Gemini with the CORRECT mime_type
        response = client.models.generate_content(
            model=model_id,
            contents=[
                final_prompt,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            ]
        )
        
        # Clean response
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        raw_data = json.loads(clean_text)
        
        final_data = clean_json_data(raw_data) if mode != "original" else raw_data
        return final_data

    except Exception as e:
        print(f"AI Error: {e}")
        # Return a visible error in the JSON so the frontend sees it
        return {"error": f"AI Processing Failed: {str(e)}"}
# --- WORD GENERATION LOGIC ---
def create_word_doc(data, filename, mode):
    try:
        if mode == "mak-tamil":
            template_name = "template_mak.docx" 
        elif mode == "original":
            template_name = "template_generic.docx" if os.path.exists("template_generic.docx") else "template.docx"
        else:
            template_name = "template.docx"
        
        if not os.path.exists(template_name):
            print(f"Error: {template_name} not found!")
            return None

        doc = DocxTemplate(template_name)
        doc.render(data)
        
        output_filename = f"Generated_{mode}_{filename}.docx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        doc.save(output_path)
        
        return output_filename
    except Exception as e:
        print(f"Word Gen Error: {e}")
        return None

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    mode = request.form.get('mode', 'both') 

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    ai_result = analyze_image_with_gemini(filepath, mode)

    if "error" in ai_result:
        return jsonify({'status': 'error', 'message': ai_result['error']})

    word_filename = create_word_doc(ai_result, filename, mode)

    if word_filename:
         return jsonify({
             'status': 'success',
             'data': ai_result,
             'download_url': word_filename 
         })
    return jsonify({'status': 'error', 'message': 'Failed to generate Word Doc.'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
