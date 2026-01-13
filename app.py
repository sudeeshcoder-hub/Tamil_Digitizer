import os
import json
import re
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from docxtpl import DocxTemplate

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")

# 2. Configure Google Gemini AI
if not API_KEY:
    print("CRITICAL ERROR: No API Key found in .env file!")
else:
    # Using 'gemini-2.5-flash' as per your setup
    genai.configure(api_key=API_KEY)

app = Flask(__name__)

# 3. Configure Folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# --- CLEANING HELPER FUNCTION (NEW) ---
def clean_option_text(text):
    """
    Removes labels like 'a)', '1.', 'A.', 'அ)', 'i)' from the start of the string.
    """
    if not text:
        return ""
    # Regex explains:
    # ^\s* -> Start of string, optional spaces
    # \(?        -> Optional opening bracket '('
    # [\w\u0B80-\u0BFF]+ -> Any Letter, Number, or Tamil Character
    # [\.\)]     -> A dot '.' or closing bracket ')'
    # \s* -> Trailing spaces
    cleaned = re.sub(r'^\s*\(?[\w\u0B80-\u0BFF]+[\.\)]\s*', '', text)
    return cleaned

def clean_json_data(data):
    """
    Goes through the entire JSON structure and cleans every option.
    """
    if "sections" in data:
        for section in data["sections"]:
            if "questions" in section:
                for q in section["questions"]:
                    if "options" in q and q["options"]:
                        # Clean every option in the list
                        q["options"] = [clean_option_text(opt) for opt in q["options"]]
    
    # Also clean for the old "choose" mode if used
    if "items" in data:
        for item in data["items"]:
            if "options" in item and item["options"]:
                item["options"] = [clean_option_text(opt) for opt in item["options"]]
                
    return data

# --- AI LOGIC ---
def analyze_image_with_gemini(image_path, mode):
    model = genai.GenerativeModel('gemini-2.5-flash') 

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
          "header": {
             "class": "...", "marks": "...", "date": "...", "time": "..."
          },
          "sections": [
            {
              "roman": "I",
              "title": "Section Title",
              "marks_eq": "6 X 1 = 6",
              "questions": [
                {
                  "no": "1",
                  "text": "Question text...",
                  "type": "mcq", 
                  "options": ["Option 1", "Option 2", "Option 3", "Option 4"] 
                }
              ]
            }
          ]
        }
        IMPORTANT: Extract options exactly as written.
        """
    elif mode == "choose":
        specific_instruction = """
        TASK: Extract ONLY MCQs.
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
    print(f"Sending to AI with mode: {mode}...") 

    try:
        sample_file = genai.upload_file(path=image_path, display_name="User Upload")
        response = model.generate_content([final_prompt, sample_file])
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        raw_data = json.loads(clean_text)
        
        # --- APPLY THE CLEANING HERE ---
        final_data = clean_json_data(raw_data)
        
        return final_data

    except Exception as e:
        print(f"AI Error: {e}")
        return {"error": str(e)}

# --- WORD GENERATION LOGIC ---
def create_word_doc(data, filename, mode):
    try:
        if mode == "mak-tamil":
            template_name = "template_mak.docx" 
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
    else:
        return jsonify({'status': 'error', 'message': 'Failed to generate Word Doc.'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)