from flask import Flask, render_template
# Importieren Sie Ihre anderen erforderlichen Module

app = Flask(__name__)
# Fügen Sie Ihre vorhandenen Flask-Routen hier hinzu

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)