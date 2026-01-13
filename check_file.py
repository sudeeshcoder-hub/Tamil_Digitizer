import os

print("Current Working Directory:", os.getcwd())
print("\nFiles in this folder:")
files = os.listdir()
for f in files:
    print(f" - {f}")

if "template.docx" in files:
    print("\n✅ SUCCESS: template.docx found!")
else:
    print("\n❌ ERROR: template.docx NOT found.")
    # Check for the double extension mistake
    if "template.docx.docx" in files:
        print("⚠️ FOUND MISTAKE: You named it 'template.docx.docx'. Rename it to 'template.docx'")