from app import app
from flask import redirect

@app.route('/proxy-to-app')
def proxy_to_app():
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
