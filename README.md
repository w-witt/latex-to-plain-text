# LaTeX to Plain Text Converter

A modern web application that converts LaTeX documents to plain text for easy reading and audio playback. Built with Flask and featuring a user-friendly interface with drag-and-drop file upload, paste functionality, and browser-based text-to-speech.

## Features

- **File Upload**: Drag and drop or click to upload `.tex` files
- **Paste Support**: Directly paste LaTeX code for conversion
- **Modern UI**: Clean, responsive interface built with Bootstrap
- **Audio Output**: Browser-based text-to-speech with adjustable speed
- **Copy/Download**: Easy copying and downloading of converted text
- **Comprehensive LaTeX Support**: Handles mathematical expressions, Greek letters, sections, and more

## LaTeX Commands Supported

- **Sections**: `\section{}`, `\section*{}`, `\subsection{}`, `\subsection*{}`
- **Greek Letters**: `\alpha`, `\beta`, `\gamma`, etc. and capital versions like `\Omega` → "capital omega"
- **Mathematical Symbols**: `\infty`, `\leq`, `\geq`, `\subset`, `\in`, etc.
- **Equations**: `\tag{}` → "equation ..."
- **Document Structure**: Ignores `\maketitle`, `\begin{}`, `\end{}`, etc.
- **And many more** - see `latex_dict.json` for the complete list

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/latex-to-plain-text.git
   cd latex-to-plain-text
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   export FLASK_APP=app.py
   flask run --reload
   ```

4. **Open your browser** and go to `http://localhost:5000`

## Usage

1. **Upload a .tex file**: Drag and drop or click to upload
2. **Or paste LaTeX code**: Use the text area to paste LaTeX directly
3. **View the output**: Plain text appears in the output box
4. **Listen to audio**: Click "Read Aloud" with adjustable speed
5. **Copy or download**: Use the buttons to save the converted text

## Project Structure

```
latex-to-plain-text/
├── app.py                 # Main Flask application
├── latex_dict.json        # LaTeX command dictionary
├── latex_dictionary.py    # Dictionary management script
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main web interface
└── README.md             # This file
```

## Dependencies

- Flask - Web framework
- pyttsx3 - Text-to-speech (for backend)
- re - Regular expressions for LaTeX parsing
- json - JSON handling for command dictionary

## Deployment

### Local Development
```bash
export FLASK_APP=app.py
flask run --reload
```

### Production Deployment
For production deployment, consider using:
- **Heroku**: Add `Procfile` and configure environment variables
- **PythonAnywhere**: Upload files and configure WSGI
- **VPS**: Use Gunicorn with Nginx
- **Docker**: Create a Dockerfile for containerization

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for the modern UI components
- Web Speech API for browser-based text-to-speech
- LaTeX community for mathematical notation standards 