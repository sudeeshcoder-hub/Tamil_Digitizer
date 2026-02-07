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
    # Using 'gemini-2.5-flash' (ensure this model is available to your API key)
    # If this fails, fallback to 'gemini-1.5-flash'
    try:
        genai.configure(api_key=API_KEY)
    except Exception as e:
         print(f"Error configuring API: {e}")

app = Flask(__name__)

# 3. Configure Folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# --- CLEANING HELPER FUNCTION ---
def clean_option_text(text):
    """
    Removes labels like 'a)', '1.', 'A.', 'அ)', 'i)' from the start of the string.
    """
    if not text:
        return ""
    # Regex explanation:
    # ^\s* -> Start of string, optional spaces
    # \(?           -> Optional opening bracket '('
    # [\w\u0B80-\u0BFF]+ -> Any Letter (English/Tamil), Number
    # [\.\)]        -> A dot '.' or closing bracket ')'
    # \s* -> Trailing spaces
    cleaned = re.sub(r'^\s*\(?[\w\u0B80-\u0BFF]+[\.\)]\s*', '', text)
    return cleaned

def clean_json_data(data):
    """
    Goes through the entire JSON structure and cleans every option to prevent duplicate labels.
    """
    # 1. Clean for "mak-tamil" mode structure
    if "sections" in data:
        for section in data["sections"]:
            if "questions" in section:
                for q in section["questions"]:
                    if "options" in q and q["options"]:
                        q["options"] = [clean_option_text(opt) for opt in q["options"]]
    
    # 2. Clean for "choose", "paragraph", "both" mode structure
    if "items" in data:
        for item in data["items"]:
            if "options" in item and item["options"]:
                item["options"] = [clean_option_text(opt) for opt in item["options"]]
                
    return data

# --- AI LOGIC ---
def analyze_image_with_gemini(image_path, mode):
    # Use the model that is active for your account. 
    # If 2.5-flash fails, change this string to 'gemini-1.5-flash'
    model = genai.GenerativeModel('gemini-2.5-flash') 

    base_instruction = """
    You are an expert Tamil Data Entry Operator.
    Analyze this image. Extract content into valid JSON.
    Do NOT use Markdown. Return raw JSON only.
    Preserve Tamil script exactly.
    """

    # --- MODE 1: MAK TAMIL QUESTION PAPER ---
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

    # --- MODE 2: ORIGINAL (STRUCTURE PRESERVING) ---
    elif mode == "original":
        specific_instruction = """
        TASK: Extract content EXACTLY as seen in the image.
        Maintain the original structure, line breaks, and formatting as much as possible.
        If it's a list, keep it as a list. If it's a paragraph, keep it as a paragraph.
        
        JSON OUTPUT FORMAT:
        {
          "items": [
            {
              "type": "original",
              "content": "Full text of the region/section...",
              "style": "text" 
            }
          ]
        }
        IMPORTANT: Do not change the text. Do not reformat. Just digitize what you see.
        """
    
    # --- MODE 3: ONLY CHOOSE ---
    elif mode == "choose":
        specific_instruction = """
        TASK: Extract ONLY Multiple Choice Questions (MCQs).
        JSON: { "items": [ { "type": "mcq", "q_no": "1", "text": "...", "options": [...] } ] }
        """
    
    # --- MODE 4: ONLY PARAGRAPH ---
    elif mode == "paragraph":
        specific_instruction = """
        TASK: Extract ONLY Paragraphs.
        JSON: { "items": [ { "type": "para", "heading": "...", "text": "..." } ] }
        """
    
    # --- MODE 5: BOTH (MIXED) ---
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
        
        # Clean the response string to get pure JSON
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        raw_data = json.loads(clean_text)
        
        # --- APPLY THE CLEANING FUNCTION HERE (Skip for 'original' mode) ---
        if mode != "original":
            final_data = clean_json_data(raw_data)
        else:
            final_data = raw_data
        
        return final_data

    except Exception as e:
        print(f"AI Error: {e}")
        return {"error": str(e)}

# --- WORD GENERATION LOGIC ---
def create_word_doc(data, filename, mode):
    try:
        # Select the correct template
        if mode == "mak-tamil":
            template_name = "template_mak.docx" 
        elif mode == "original":
            # Check if a generic template exists, otherwise use default
            if os.path.exists("template_generic.docx"):
                template_name = "template_generic.docx"
            else:
                template_name = "template.docx"
        else:
            template_name = "template.docx"
        
        if not os.path.exists(template_name):
            print(f"Error: {template_name} not found! Run fix_template.py first.")
            return None

        doc = DocxTemplate(template_name)
        
        # Render the data into the template
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

    # 1. Analyze with AI
    ai_result = analyze_image_with_gemini(filepath, mode)

    if "error" in ai_result:
        return jsonify({'status': 'error', 'message': ai_result['error']})

    # 2. Generate Word Doc
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
    # Using '0.0.0.0' makes it accessible externally if needed (e.g. Docker/Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)