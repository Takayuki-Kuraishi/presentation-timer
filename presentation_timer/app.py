from flask import Flask, render_template, send_from_directory
import os

app = Flask(__name__)

# テンプレートのパスを明示的に指定
template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    try:
        return send_from_directory('audio', filename)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    print(f"Template directory: {template_dir}")
    print(f"Current working directory: {os.getcwd()}")
    app.run(host='0.0.0.0', port=5000, debug=True)