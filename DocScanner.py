import os
from flask import Flask, request, render_template, send_from_directory
from werkzeug.utils import secure_filename
import PyPDF2
import spacy

app = Flask(__name__)

# Ensure the spaCy model is loaded once
nlp = spacy.load("en_core_web_lg")

def extract_text_from_pdf(pdf_path):
    """Extract text from a given PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    print(f"Text extraction failed on page {reader.pages.index(page) + 1}")
            return text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def search_phrases(doc, phrases):
    """Search for phrases using semantic similarity and return matches."""
    matches = {}
    target_docs = {phrase: nlp(phrase) for phrase in phrases}  # Preprocess target phrases once
    for sentence in doc.sents:
        for phrase, target_doc in target_docs.items():
            # Compare each sentence to the target phrase
            if sentence.similarity(target_doc) > 0.95:  # Adjust similarity threshold as needed
                # If the sentence is similar to the phrase, add it to the matches
                matches.setdefault(phrase, []).append(sentence.text)
    return matches

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        phrases = request.form['phrases'].split(';')
        if file and all(phrase.strip() for phrase in phrases):
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            pdf_text = extract_text_from_pdf(file_path)
            if pdf_text is None:
                return "Failed to extract text from PDF."
            document = nlp(pdf_text)
            results = search_phrases(document, phrases)
            return render_template('results.html', results=results, filename=filename)
    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)