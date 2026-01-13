# Tamil & English Question Paper Digitizer

A Python-based web application that converts handwritten Tamil/English question papers into structured, editable Microsoft Word documents using Google Gemini AI.

## Features
* **AI-Powered OCR:** Uses Gemini 2.5 Flash to read handwriting.
* **Smart Parsing:** Distinguishes between MCQs and Paragraphs.
* **Auto-Formatting:** Generates a "MAK Group of Schools" style Word document automatically.
* **Narrow Margins & Formatting:** Custom template generation with Nirmala UI font.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/Tamil_Digitizer.git](https://github.com/YOUR_USERNAME/Tamil_Digitizer.git)
   cd Tamil_Digitizer
2. pip install -r requirements.txt
3. GENAI_API_KEY=your_actual_api_key_here
4. python fix_template.py
5. python app.py

#### **Step 3: Freeze Dependencies**
This creates a list of all the libraries your project uses so others can install them easily.
1.  Open your Terminal (ensure `venv` is active).
2.  Run this command:
    ```bash
    pip freeze > requirements.txt
    ```

---

### **Phase 2: Initialize Git (The Local Part)**

Now we turn your folder into a Git repository.

1.  **Open Terminal** in VS Code.
2.  **Initialize Git:**
    ```bash
    git init
    ```
3.  **Add Your Files:**
    ```bash
    git add .
    ```
    *(Note: If you created the `.gitignore` correctly, this command will NOT add `venv` or `.env`. You can check by typing `git status` - you should not see them listed).*
4.  **Commit the Changes:**
    ```bash
    git commit -m "Initial commit - Tamil Digitizer V1"
    ```

---

