import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv
from utils.azure_connect import get_all_messages, delete_messages_by_info

app = Flask(__name__)
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

DUMMY_USER = "dummy"
DUMMY_PASS = "dummy"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        if user == DUMMY_USER and pwd == DUMMY_PASS:
            session["user"] = DUMMY_USER
            session["dummy"] = True
            return redirect(url_for("dashboard"))

        if user == USERNAME and pwd == PASSWORD:
            session["user"] = user
            session["dummy"] = False
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("dummy"):
        # Dummy data for guest users
        messages = [
            {"name": "Rahul Jaikar", "email": "rahul@yahoo.com", "message": "Aarohiiii....", "date": "2024-06-01", "time": "12:00:00", "partition_key": "john@example.com", "row_key": "12:00:00"},
            {"name": "Heera Thakur", "email": "heera@rediffmail.com", "message": "Aapke tiraskar ko aashirwaad samajh kar ja rha hoon", "date": "2024-06-02", "time": "14:30:00", "partition_key": "jane@example.com", "row_key": "14:30:00"},
        ]
        return render_template("dashboard.html", messages=messages, user="Guest (Dummy Mode)")
    
    messages = get_all_messages()
    return render_template("dashboard.html", messages=messages, user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("dummy", None)
    return redirect(url_for("login"))

@app.route("/delete", methods=["POST"])
def delete_messages():
    if "user" not in session:
        return jsonify({"status": "unauthorized"}), 401

    if session.get("dummy"):
        return jsonify({"status": "success"})  # Pretend delete for dummy user

    data = request.get_json()
    to_delete = data.get("messages", [])

    success = delete_messages_by_info(to_delete)

    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    app.run(debug=True)