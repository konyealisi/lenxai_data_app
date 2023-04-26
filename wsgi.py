from app import app
from dashboard import app as dash_app

app.wsgi_app = dash_app.server

if __name__ == '__main__':
    app.run(debug=True)
