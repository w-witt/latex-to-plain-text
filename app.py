import json
import re
import pyttsx3
import os
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
import webbrowser
import threading
import time
import fitz  # PyMuPDF
from PIL import Image
import torch
from transformers import AutoModelForVision2Seq, AutoProcessor

class LatexToAudio:
    def __init__(self, dictionary_file="latex_dict.json"):
        self.dictionary_file = dictionary_file
        self.commands = {}
        self.load_dictionary()
        self.engine = pyttsx3.init()

    def load_dictionary(self):
        with open(self.dictionary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.commands = data.get('commands', {})

    def get_plain_text(self, latex_command):
        return self.commands.get(latex_command)

    def parse_latex(self, tex_content):
        # Remove preamble (everything before \begin{document})
        tex_content = re.sub(r'^.*?\\begin{document}', '', tex_content, flags=re.DOTALL)
        # Remove \end{document} and everything after it
        tex_content = re.sub(r'\\end{document}.*$', '', tex_content, flags=re.DOTALL)
        # Remove document class and begin/end document
        tex_content = re.sub(r'\\documentclass{.*?}', '', tex_content)
        tex_content = re.sub(r'\\begin{document}|\\end{document}', '', tex_content)
        # Ignore (remove) \maketitle
        tex_content = re.sub(r'\\maketitle', '', tex_content)
        # Ignore (remove) \left and \right
        tex_content = re.sub(r'\\left', '', tex_content)
        tex_content = re.sub(r'\\right', '', tex_content)

        # Handle \section*{} and \section{} as "Section"
        tex_content = re.sub(r'\\section\*?{([^}]+)}', r'Section \1', tex_content)
        # Handle \subsection*{} and \subsection{} as "Sub-section"
        tex_content = re.sub(r'\\subsection\*?{([^}]+)}', r'Sub-section \1', tex_content)

        # Ignore \textwidth
        tex_content = re.sub(r'\\textwidth', '', tex_content)

        # Ignore \begin{} and \end{}
        tex_content = re.sub(r'\\begin{[^}]+}|\\end{[^}]+}', '', tex_content)

        # Handle \item as "item"
        tex_content = re.sub(r'\\item', 'item', tex_content)

        # Replace '$' with '\( ' and '\)' for consistent handling
        tex_content = re.sub(r'\$', r'\\( ', tex_content)
        tex_content = re.sub(r'\$', r'\\)', tex_content)

        # Handle \| ... \|^{2} or \| ... \|^2 as "the two norm of ..."
        tex_content = re.sub(r'\\\|(.+?)\\\|\s*(\^\{?2\}?)', r'the two norm of \1', tex_content)
        # Handle \| ... \| (norms) - non-greedy match
        tex_content = re.sub(r'\\\|(.+?)\\\|', r'the norm of \1', tex_content)

        # Handle \mathbb{R}
        tex_content = re.sub(r'\\mathbb{R}', 'the reals', tex_content)

        # Handle \{ ... \} for sets/sequences
        tex_content = re.sub(r'\\\{(.+?)\\\}', r'the sequence \1', tex_content)

        # Dictionary of replacements for common LaTeX math symbols
        replacements = [
            (r'\\infty', 'infinity'),
            (r'\\subset', 'subset of'),
            (r'\\supset', 'superset of'),
            (r'\\leq', 'less than or equal to'),
            (r'\\geq', 'greater than or equal to'),
            (r'\\le', 'less than or equal to'),
            (r'\\ge', 'greater than or equal to'),
            (r'\\to', 'approaches'),
            (r'\\cdots', 'dot dot dot'),
            (r'\\ldots', 'dot dot dot'),
            (r'\\in', 'element of'),
            (r'\\dots', 'dot dot dot'),
            (r'\\forall', 'for all'),
            (r'\\exists', 'there exists'),
            (r'\\neq', 'not equal to'),
            (r'\\pm', 'plus or minus'),
            (r'\\mp', 'minus or plus'),
            (r'\\times', 'times'),
            (r'\\div', 'divided by'),
            (r'\\cup', 'union'),
            (r'\\cap', 'intersection'),
            (r'\\emptyset', 'empty set'),
            (r'\\Rightarrow', 'implies'),
            (r'\\implies', 'implies'),
            (r'\\iff', 'if and only if'),
            (r'<', 'less than'),
            (r'>', 'greater than'),
            (r'\|([^|]+)\|', r'absolute value of \1'),
        ]
        for pattern, plain in replacements:
            tex_content = re.sub(pattern, plain, tex_content)

        # Handle ^{\prime} and ^\prime as "prime"
        tex_content = re.sub(r'\^\{\\prime\}', ' prime', tex_content)
        tex_content = re.sub(r'\^\\prime', ' prime', tex_content)

        # Handle subscripts and superscripts (both {...} and single char)
        tex_content = re.sub(r'_([a-zA-Z0-9])', r' sub \1', tex_content)
        tex_content = re.sub(r'_{([^}]+)}', r' sub \1', tex_content)
        tex_content = re.sub(r'\^([a-zA-Z0-9])', r' to the power of \1', tex_content)
        tex_content = re.sub(r'\^{([^}]+)}', r' to the power of \1', tex_content)

        # Add spaces around minus and plus signs (robust)
        tex_content = re.sub(r'(?<=\w)-(?=\w)', ' minus ', tex_content)
        tex_content = re.sub(r'(?<=\w)\+(?=\w)', ' plus ', tex_content)

        # Handle = in math context
        tex_content = tex_content.replace('=', ' equals ')

        # Clean up math mode delimiters
        tex_content = tex_content.replace(r'\(', '').replace(r'\)', '')
        tex_content = tex_content.replace(r'\[', '').replace(r'\]', '')

        # Clean up extra whitespace
        tex_content = re.sub(r'\s+', ' ', tex_content).strip()

        # Ignore \quad
        tex_content = re.sub(r'\\quad', '', tex_content)

        # Ensure spaces between items in mathematical expressions
        tex_content = re.sub(r'([a-zA-Z0-9])([<>=+\-])', r'\1 \2', tex_content)
        tex_content = re.sub(r'([<>=+\-])([a-zA-Z0-9])', r'\1 \2', tex_content)

        # Handle capital Greek letters as 'capital ...'
        capital_greek = [
            'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega'
        ]
        for letter in capital_greek:
            tex_content = re.sub(rf'\\{letter}\b', f'capital {letter.lower()}', tex_content)

        # Handle \tag{...} as 'equation ...'
        tex_content = re.sub(r'\\tag{([^}]+)}', r'equation \1', tex_content)

        return tex_content

    def read_file(self, tex_file):
        with open(tex_file, 'r', encoding='utf-8') as f:
            tex_content = f.read()
        plain_text = self.parse_latex(tex_content)
        print("\nPlain text output:")
        print("-" * 50)
        print(plain_text)
        print("-" * 50)
        print("\nReading text aloud...")
        self.engine.say(plain_text)
        self.engine.runAndWait()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'tex', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize Nougat model and processor
model = None
processor = None

def load_nougat_model():
    """Load the Nougat model and processor."""
    global model, processor
    if model is None or processor is None:
        try:
            model = AutoModelForVision2Seq.from_pretrained(
                "facebook/nougat-base",
                device_map="auto",
                trust_remote_code=True
            )
            processor = AutoProcessor.from_pretrained(
                "facebook/nougat-base",
                trust_remote_code=True
            )
            model.eval()
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            return False
    return True

def process_pdf_with_nougat(pdf_file):
    """Process PDF and convert to LaTeX using Nougat."""
    if not load_nougat_model():
        return None, "Failed to load Nougat model"

    try:
        pdf_document = fitz.open(stream=pdf_file.read(), filetype="pdf")
        latex_pages = []
        
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            with torch.no_grad():
                inputs = processor(images=img, return_tensors="pt")
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
                outputs = model.generate(
                    **inputs,
                    max_length=4096,
                    num_beams=2,
                    early_stopping=True
                )
                output = processor.batch_decode(outputs, skip_special_tokens=True)[0]
            latex_pages.append(output)
        
        return "\n\n".join(latex_pages), None
    except Exception as e:
        return None, str(e)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        tex_content = file.read().decode('utf-8')
        return jsonify({'tex_content': tex_content})
    return jsonify({'error': 'Unknown error'}), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    plain_text = ''
    tex_content = ''
    audio_file = None
    speed = request.form.get('speed', '150')
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            with open(file_path, 'r', encoding='utf-8') as f:
                tex_content = f.read()
            converter = LatexToAudio()
            plain_text = converter.parse_latex(tex_content)
            # Generate audio file
            engine = pyttsx3.init()
            engine.setProperty('rate', int(speed))
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + '.mp3')
            engine.save_to_file(plain_text, audio_path)
            engine.runAndWait()
            if os.path.exists(audio_path):
                audio_file = filename + '.mp3'
            return render_template('index.html', tex_content=tex_content, plain_text=plain_text, audio_file=audio_file, speed=speed)
        else:
            return render_template('index.html', error='Invalid file type. Please upload a .tex file.', tex_content='', plain_text='', audio_file=None, speed=speed)
    return render_template('index.html', tex_content=tex_content, plain_text=plain_text, audio_file=audio_file, speed=speed)

@app.route('/audio/<filename>')
def audio(filename):
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    return send_file(audio_path, as_attachment=True)

@app.route('/paste', methods=['GET', 'POST'])
def paste():
    plain_text = ''
    tex_content = ''
    audio_file = None
    speed = request.form.get('speed', '150')
    if request.method == 'POST':
        tex_content = request.form.get('tex_content', '')
        if tex_content:
            converter = LatexToAudio()
            plain_text = converter.parse_latex(tex_content)
            # Generate audio file
            engine = pyttsx3.init()
            engine.setProperty('rate', int(speed))
            audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pasted.tex.mp3')
            engine.save_to_file(plain_text, audio_path)
            engine.runAndWait()
            if os.path.exists(audio_path):
                audio_file = 'pasted.tex.mp3'
            return render_template('paste.html', tex_content=tex_content, plain_text=plain_text, audio_file=audio_file, speed=speed)
    return render_template('paste.html', tex_content=tex_content, plain_text=plain_text, audio_file=audio_file, speed=speed)

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        if not data or 'tex_content' not in data:
            return jsonify({
                'error': 'No TeX content provided',
                'plain_text': '',
                'audio_file': None
            }), 400

        tex_content = data['tex_content']
        if not tex_content.strip():
            return jsonify({
                'error': 'Empty TeX content',
                'plain_text': '',
                'audio_file': None
            }), 400

        converter = LatexToAudio()
        plain_text = converter.parse_latex(tex_content)
        
        # Generate audio file
        engine = pyttsx3.init()
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'converted.tex.mp3')
        engine.save_to_file(plain_text, audio_path)
        engine.runAndWait()

        response_data = {
            'plain_text': plain_text,
            'audio_file': '/audio/converted.tex.mp3' if os.path.exists(audio_path) else None
        }
        
        print("Sending response:", response_data)  # Debug log
        return jsonify(response_data)

    except Exception as e:
        print("Error in convert route:", str(e))  # Debug log
        return jsonify({
            'error': str(e),
            'plain_text': '',
            'audio_file': None
        }), 500

def open_browser():
    time.sleep(1.5)  # Wait for the server to start
    webbrowser.open('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=True) 