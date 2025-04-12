import pyrebase
from flask import Flask, render_template, request, redirect, url_for, session, flash
import firebase_admin
from firebase_admin import credentials, auth, firestore
from flask_mysqldb import MySQL
import os
from werkzeug.utils import secure_filename
from flask import jsonify
from flask_cors import CORS


app = Flask(__name__)
CORS(app) 
app.secret_key = "vibescreen_secret_key"


cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

config = {
    "apiKey": "AIzaSyBN9rp84gIRet6jdUEjjQTUqPxB3BWgIsw",
    "authDomain": "com.melky.com",
    "databaseURL": "https://melky-firebase-default-rtdb.firebaseio.com/",
    "projectId": "melky-firebase",
    "storageBucket": "YOUR_STORAGE_BUCKET",
    "messagingSenderId": "417468427084",
    "appId": "1:417468427084:android:05a16043015168773dfde9",
    "measurementId": "YOUR_MEASUREMENT_ID"
}

firebase = pyrebase.initialize_app(config)
auth_pyrebase = firebase.auth()

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'vibe_screen'
mysql = MySQL(app)

UPLOAD_FOLDER = 'static/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def is_admin():
    return "user" in session and session["user"].get("role") == "admin"

@app.route("/")
def home():
    if not is_admin():
        return redirect(url_for("login"))
    return render_template("home.html", username=session["user"]["username"])

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("register.html", error="Password tidak cocok!")

        try:
            user = auth_pyrebase.create_user_with_email_and_password(email, password)
            user_data = {"username": username, "email": email, "role": "admin"}
            db.collection("users").document(user["localId"]).set(user_data)
            flash("Registrasi berhasil! Silakan login.", "success")
            return render_template("register.html", success=True)
        except Exception as e:
            error_msg = str(e)
            if "EMAIL_EXISTS" in error_msg:
                return render_template("register.html", error="Email sudah terdaftar.")
            elif "WEAK_PASSWORD" in error_msg:
                return render_template("register.html", error="Password minimal 6 karakter.")
            else:
                return render_template("register.html", error=error_msg)

    return render_template("register.html")

@app.route("/films")
def films():
    if not is_admin():
        return redirect(url_for("login"))

    query = request.args.get("q")
    cursor = mysql.connection.cursor()

    if query:
        sql = "SELECT * FROM films WHERE title LIKE %s"
        cursor.execute(sql, ("%" + query + "%",))
    else:
        cursor.execute("SELECT * FROM films")

    films = cursor.fetchall()
    cursor.close()
    return render_template("film.html", films=films)

@app.route("/add_film", methods=["POST"])
def add_film():
    if not is_admin():
        return redirect(url_for("login"))
    title = request.form["title"]
    mood = request.form["mood"] 
    genre = request.form["genre"]
    description = request.form["description"]
    release_year = request.form["release_year"]
    rating = request.form["rating"]
    image_url = request.form.get("image_url", "")
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO films (title, mood, genre, description, release_year, rating, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                   (title,mood, genre, description, release_year, rating, image_url))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("films"))

@app.route('/edit_film/<int:id>', methods=['GET', 'POST'])
def edit_film(id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        # Ambil data dari form dengan nama yang sama seperti di HTML
        title = request.form['title']
        mood = request.form['mood']
        genre = request.form['genre']
        release_year = request.form['release_year']
        description = request.form['description']
        rating = request.form['rating']
        image_url = request.form['image_url']

        # Update ke database
        cur.execute("""
            UPDATE films
            SET title = %s, mood = %s, genre = %s, release_year = %s, description = %s, rating = %s, image_url = %s
            WHERE id = %s
        """, (title, mood, genre, release_year, description, rating, image_url, id))
        mysql.connection.commit()
        cur.close()
        flash('Film berhasil diperbarui!', 'success')
        return redirect(url_for('films'))

    else:
        # Ambil data film berdasarkan ID (urutan kolom harus sesuai dengan HTML form)
        cur.execute("SELECT id, title, mood, genre, release_year, description, rating, image_url FROM films WHERE id = %s", (id,))
        film = cur.fetchone()
        cur.close()

        if film:
            return render_template('edit_film.html', film=film)
        else:
            flash('Film tidak ditemukan.', 'danger')
            return redirect(url_for('films'))


@app.route("/delete_film/<int:id>", methods=["POST"])
def delete_film(id):
    if not is_admin():
        return redirect(url_for("login"))
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM films WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("films"))

@app.route("/music")
def music():
    if not is_admin():
        return redirect(url_for("login"))

    query = request.args.get("q")
    cursor = mysql.connection.cursor()

    if query:
        sql = "SELECT * FROM musik WHERE title LIKE %s"
        cursor.execute(sql, ("%" + query + "%",))
    else:
        cursor.execute("SELECT * FROM musik")

    music = cursor.fetchall()
    cursor.close()
    return render_template("musik.html", music=music)

@app.route("/add_music", methods=["POST"])
def add_music():
    if not is_admin():
        return redirect(url_for("login"))
    title = request.form["title"]
    mood = request.form["mood"] 
    artist = request.form["artist"]
    album = request.form["album"]
    release_year = request.form["release_year"]
    genre = request.form["genre"]
    rating = request.form["rating"]
    image_url = request.form.get("image_url", "")

    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO musik (title, mood, artist, album, release_year, genre, rating, image_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (title, mood, artist, album, release_year, genre, rating, image_url))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("music"))

@app.route("/edit_music/<int:id>", methods=["GET", "POST"])
def edit_music(id):
    if not is_admin():
        return redirect(url_for("login"))
    cursor = mysql.connection.cursor()
    if request.method == "POST":
        title = request.form["title"]
        mood = request.form["mood"] 
        artist = request.form["artist"]
        album = request.form["album"]
        release_year = request.form["release_year"]
        genre = request.form["genre"]
        rating = request.form["rating"]
        image_url = request.form.get("image_url", "")
        cursor.execute("""
            UPDATE musik
            SET title=%s, mood=%s, artist=%s, album=%s, release_year=%s, genre=%s, rating=%s, image_url=%s
            WHERE id=%s
        """, (title, mood, artist, album, release_year, genre, rating, image_url, id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("music"))

    cursor.execute("SELECT * FROM musik WHERE id = %s", (id,))
    music = cursor.fetchone()
    cursor.close()
    return render_template("edit_music.html", music=music)

@app.route("/delete_music/<int:id>", methods=["POST"])
def delete_music(id):
    if not is_admin():
        return redirect(url_for("login"))
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM musik WHERE id = %s", (id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for("music"))

@app.route("/profile")
def profile():
    if not is_admin():
        return redirect(url_for("login"))
    return render_template("profile.html", user=session["user"])


@app.route("/edit_profile", methods=["POST"])
def edit_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    username = request.form["username"]
    profile_picture = request.files["profile_picture"]

    user_data = session["user"]
    user_id = user_data["email"]

    if profile_picture and profile_picture.filename != "":
        filename = secure_filename(profile_picture.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        profile_picture.save(file_path)
        profile_url = f"/{file_path}"
        user_data["profile_picture"] = profile_url
    else:
        profile_url = user_data.get("profile_picture", "")

    session["user"]["username"] = username
    session["user"]["profile_picture"] = profile_url

    user_docs = db.collection("users").where("email", "==", user_data["email"]).get()
    for doc in user_docs:
        doc.reference.update({
            "username": username,
            "profile_picture": profile_url
        })

    flash("Profil berhasil diperbarui!", "success")
    return redirect(url_for("profile"))

import requests

import requests

# Ini yang penting
api_key = "AIzaSyBN9rp84gIRet6jdUEjjQTUqPxB3BWgIsw"

@app.route("/change_password", methods=["POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("login"))

    email = session["user"]["email"]
    old_password = request.form["old_password"]
    new_password = request.form["new_password"]
    confirm_password = request.form["confirm_password"]

    if new_password != confirm_password:
        flash("Password baru dan konfirmasi tidak cocok.", "error")
        return redirect(url_for("profile"))

    if len(new_password) < 6:
        flash("Password baru harus minimal 6 karakter.", "error")
        return redirect(url_for("profile"))

    try:
        # login dulu buat dapetin idToken
        user = auth_pyrebase.sign_in_with_email_and_password(email, old_password)
        id_token = user["idToken"]

        # pakai REST API untuk update password
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={api_key}"
        payload = {
            "idToken": id_token,
            "password": new_password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        result = response.json()

        if "error" in result:
            raise Exception(result["error"]["message"])

        flash("Password berhasil diubah!", "success")
    except Exception as e:
        flash("Gagal mengganti password: " + str(e), "error")

    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            user = auth_pyrebase.sign_in_with_email_and_password(email, password)
            uid = user["localId"]
            user_data = db.collection("users").document(uid).get().to_dict()
            if user_data.get("role") != "admin":
                return render_template("login.html", error="Akses hanya untuk admin!")
            session["user"] = {"username": user_data["username"], "email": email, "role": user_data["role"]}
            return redirect(url_for("home"))
        except:
            return render_template("login.html", error="Email atau password salah!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))



# Flask route
@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    mood = data.get('mood')

    # Lakukan query ke MySQL untuk mendapatkan film dan musik berdasarkan mood
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM films WHERE mood = %s", (mood,))
    films = cursor.fetchall()

    cursor.execute("SELECT * FROM musik WHERE mood = %s", (mood,))
    music = cursor.fetchall()
    cursor.close()

    return jsonify({
        'films': [dict(zip(('id', 'title', 'mood', 'genre', 'description', 'release_year', 'rating', 'image_url'), film)) for film in films],
        'music': [dict(zip(('id', 'title', 'mood', 'artist', 'album', 'release_year', 'genre', 'rating', 'image_url'), m)) for m in music]
    })

@app.route("/films_user", methods=["GET"])
def get_all_films():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, title, mood, genre, description, release_year, rating, image_url FROM films")
    rows = cursor.fetchall()
    cursor.close()

    films = []
    for row in rows:
        films.append({
            "id": row[0],
            "title": row[1],
            "mood": row[2],
            "genre": row[3],
            "description": row[4],
            "release_year": row[5],
            "rating": float(row[6]),
            "image_url": row[7]
        })

    return jsonify(films)


@app.route('/music_user')
def get_music():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM musik")
    results = cursor.fetchall()
    cursor.close()
    return jsonify([
        dict(zip(('id', 'title', 'mood', 'artist', 'album', 'release_year', 'genre', 'rating', 'image_url'), row))
        for row in results
    ])

# @app.route("/analyze_sentiment", methods=["POST"])
# def analyze_sentiment():
#     text = request.json.get("text", "").lower()
#     # Sederhana: bisa kamu ganti dengan model ML nanti
#     if any(word in text for word in ["happy", "senang", "excited", "gembira"]):
#         mood = "happy"
#     elif any(word in text for word in ["sad", "sedih", "galau", "murung","kecewa"]):
#         mood = "sad"
#     elif any(word in text for word in ["chill", "tenang", "santai","biasa"]):
#         mood = "flat"
#     else:
#         mood = "neutral"
#     return jsonify({"mood": mood})


# ini algoritma yang bener

from transformers import pipeline
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="w11wo/indonesian-roberta-base-sentiment-classifier"
)


# Fungsi untuk mengubah label ke mood
def convert_label_to_mood(label):
    label = label.lower()
    if label == "positive":
        return "happy"
    elif label == "negative":
        return "sad"
    else:
        return "neutral"

@app.route('/analyze_sentiment', methods=['POST'])
def recommend_from_text():
    data = request.json
    user_text = data.get('text')

    if not user_text:
        return jsonify({'error': 'Text is required'}), 400

    # Analisis sentimen menggunakan IndoBERT
    result = sentiment_pipeline(user_text)[0]
    label = result['label']
    mood = convert_label_to_mood(label)

    # Query film dan musik berdasarkan mood
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM films WHERE mood = %s", (mood,))
    films = cursor.fetchall()

    cursor.execute("SELECT * FROM musik WHERE mood = %s", (mood,))
    music = cursor.fetchall()
    cursor.close()

    return jsonify({
        'text': user_text,
        'mood': mood,
        'films': [dict(zip(('id', 'title', 'mood', 'genre', 'description', 'release_year', 'rating', 'image_url'), film)) for film in films],
        'music': [dict(zip(('id', 'title', 'mood', 'artist', 'album', 'release_year', 'genre', 'rating', 'image_url'), m)) for m in music]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

