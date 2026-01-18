from flask import Flask, render_template

from routes.admin import admin_routes
from routes.user import user_routes
from routes.user_current_bookings import user_bookings
from utils.formatDateTime import format_datetime

app = Flask(__name__)
app.secret_key = "smart-parking-secret-key"

app.register_blueprint(admin_routes)
app.register_blueprint(user_routes)
app.register_blueprint(user_bookings)
app.jinja_env.filters["format_datetime"] = format_datetime

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/temp")
def temp():
    return render_template("temp.html")


if __name__ == "__main__":
    app.run(debug=True)
