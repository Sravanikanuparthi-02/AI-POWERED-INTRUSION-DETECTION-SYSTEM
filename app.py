from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3
from datetime import datetime
import pickle
import os

app = Flask(__name__)
app.secret_key = "intrusion_secret_key"


# ---------------- DB ----------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            flow_duration REAL,
            total_fwd_packets REAL,
            total_backward_packets REAL,
            flow_bytes_s REAL,
            flow_packets_s REAL,
            fwd_pkt_len_mean REAL,
            bwd_pkt_len_mean REAL,
            destination_port INTEGER,
            protocol INTEGER,
            prediction TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- LOAD ML MODEL ----------------
MODEL_FILE = os.path.join("model", "ids_model.pkl")

ml_package = None
if os.path.exists(MODEL_FILE):
    with open(MODEL_FILE, "rb") as f:
        ml_package = pickle.load(f)


def predict_intrusion(data_dict):
    """
    Returns prediction label string
    """
    if ml_package is None:
        return "MODEL_NOT_FOUND"

    model = ml_package["model"]
    scaler = ml_package["scaler"]
    le = ml_package["label_encoder"]
    feature_cols = ml_package["feature_cols"]

    X = [[data_dict[col] for col in feature_cols]]
    X_scaled = scaler.transform(X)
    pred = model.predict(X_scaled)[0]
    label = le.inverse_transform([pred])[0]
    return label


# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           (name, email, password))
            conn.commit()
            flash("Registration successful! Please login.", "success")
            return redirect("/login")
        except:
            flash("Email already exists!", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect("/dashboard")
        else:
            flash("Invalid login details!", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect("/login")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html")


@app.route("/add_log", methods=["GET", "POST"])
def add_log():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        data_dict = {
            "Flow Duration": float(request.form["flow_duration"]),
            "Total Fwd Packets": float(request.form["total_fwd_packets"]),
            "Total Backward Packets": float(request.form["total_backward_packets"]),
            "Flow Bytes/s": float(request.form["flow_bytes_s"]),
            "Flow Packets/s": float(request.form["flow_packets_s"]),
            "Fwd Packet Length Mean": float(request.form["fwd_pkt_len_mean"]),
            "Bwd Packet Length Mean": float(request.form["bwd_pkt_len_mean"]),
            "Destination Port": int(request.form["destination_port"]),
            "Protocol": int(request.form["protocol"])
        }

        prediction = predict_intrusion(data_dict)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO logs (
                flow_duration, total_fwd_packets, total_backward_packets,
                flow_bytes_s, flow_packets_s, fwd_pkt_len_mean,
                bwd_pkt_len_mean, destination_port, protocol,
                prediction, timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data_dict["Flow Duration"],
            data_dict["Total Fwd Packets"],
            data_dict["Total Backward Packets"],
            data_dict["Flow Bytes/s"],
            data_dict["Flow Packets/s"],
            data_dict["Fwd Packet Length Mean"],
            data_dict["Bwd Packet Length Mean"],
            data_dict["Destination Port"],
            data_dict["Protocol"],
            prediction,
            timestamp
        ))

        conn.commit()
        conn.close()

        flash(f"Log added! Prediction: {prediction}", "success")
        return redirect("/logs")

    return render_template("add_log.html")


@app.route("/logs")
def logs():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM logs ORDER BY id DESC")
    logs_data = cursor.fetchall()
    conn.close()

    return render_template("logs.html", logs=logs_data)


# ---------------- API FOR CHART DATA ----------------
@app.route("/chart-data")
def chart_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT prediction, COUNT(*) as count
        FROM logs
        GROUP BY prediction
    """)
    rows = cursor.fetchall()
    conn.close()

    labels = [r["prediction"] for r in rows]
    counts = [r["count"] for r in rows]

    return jsonify({"labels": labels, "counts": counts})


if __name__ == "__main__":
    app.run(debug=True)