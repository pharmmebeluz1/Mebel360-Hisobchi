import os
import json
import webbrowser
from threading import Timer
from flask import Flask, jsonify, request

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, '2DPLACE_EXPORT')
CONFIG_FILE = os.path.join(BASE_DIR, '2dplace_config.json')

os.makedirs(EXPORT_DIR, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"default_material": "LDSP 16mm", "saw_blade": 4, "trim": 10}

@app.route('/')
def index():
    html_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h3>index.html fayli topilmadi!</h3>"

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/export-2dplace', methods=['POST'])
def export_to_2dplace():
    try:
        data = request.json or {}
        filename = data.get('filename', '2DPLACE_IMPORT.txt')
        parts = data.get('parts', [])

        if not parts:
            return jsonify({'success': False, 'message': 'Detallar topilmadi!'}), 400

        filepath = os.path.join(EXPORT_DIR, filename)
        
        # 2D Place formati (Nomi \t Uzunlik \t Kenglik \t Soni \t Material)
        lines = []
        for p in parts:
            name = p.get('name', 'Detall')
            length = p.get('length', 0)
            width = p.get('width', 0)
            qty = p.get('qty', 1)
            material = p.get('material', 'LDSP 16mm')
            lines.append(f"{name}\t{length}\t{width}\t{qty}\t{material}")

        content = "\n".join(lines)
        try:
            with open(filepath, 'w', encoding='cp1251') as f:
                f.write(content)
        except UnicodeEncodeError:
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write(content)

        return jsonify({
            'success': True,
            'message': f"Fayl saqlandi: 2DPLACE_EXPORT/{filename}",
            'path': filepath
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    Timer(1.5, open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)