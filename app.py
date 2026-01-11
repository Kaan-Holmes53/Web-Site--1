from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import json, os, bcrypt
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_key"

DATA_FILE = "users.json"
TOPIC_FILE = "general_topics.json"
LOG_FILE = "logs.json"


# ---------------------------
# 🛡 LOG SİSTEMİ
# ---------------------------

@app.route("/admin/logs")
def admin_logs():
    # Kullanıcı admin değilse giriş verme
    if "role" not in session or session["role"] != "admin":
        flash("Bu sayfaya sadece adminler erişebilir!", "error")
        return redirect(url_for("main"))

    # log.json dosyasını yükle
    if not os.path.exists(LOG_FILE):
        logs = []
    else:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except:
                logs = []

    # log.html dosyasına gönder
    return render_template("log.html", logs=logs)


def save_log(ip, endpoint):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = {"ip": ip, "endpoint": endpoint, "time": timestamp}

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    data.append(log)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@app.before_request
def log_request():
    ip = request.remote_addr
    endpoint = request.path
    save_log(ip, endpoint)


# ---------------------------
# Ana Sayfa
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------
# Dosyalar yoksa oluştur
# ---------------------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

if not os.path.exists(TOPIC_FILE):
    with open(TOPIC_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)

# ---------------------------
# Kullanıcı yardımcıları
# ---------------------------
def load_users():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


# ---------------------------
# DOSYA İNDİRME
# ---------------------------
@app.route("/kural-indir")
def kural_indir():
    return send_from_directory(
        directory="downloads",
        path="CloneRolePlay_Kurallari.docx",
        as_attachment=True
    )


# ---------------------------
# Resmi rotalar
# ---------------------------
@app.route("/kurallar")
def kural():
    return render_template("resmi1.html")

@app.route("/başvuru")
def başvuru():
    return render_template("resmi2.html")

@app.route("/öneri")
def öneri():
    return render_template("resmi3.html")


# ---------------------------
# MAIN SAYFA
# ---------------------------
@app.route("/main")
def main():
    if "username" not in session:
        flash("Bu sayfaya erişmek için giriş yapmalısın!", "error")
        return redirect(url_for("home"))

    users = load_users()

    # Giriş yapmış adminleri bul
    aktif_adminler = []
    for username, info in users.items():
        if info.get("role") == "admin":
            aktif_adminler.append(username)

    # Tüm konuları yükle
    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        general_topics = json.load(f)

    # POPÜLER KONULARI HESAPLA
    sorted_topics = sorted(
        general_topics,
        key=lambda x: x.get("visit_count", 0),
        reverse=True
    )

    topPopularTopics = sorted_topics[:3]

    # Resmi konular
    resmi_konular = [
        {"title": "Clone RolePlay Kuralları", "author": "Kaan", "role": "Admin", "date": "14.11.25", "link": "kurallar"},
        {"title": "Yetkili Başvuruları", "author": "Kaan", "date": "14.11.25", "link": "başvuru"},
        {"title": "Yeni Özellik Önerileri", "author": "Kaan", "date": "14.11.25", "link": "öneri"},
    ]

    return render_template(
        "main.html",
        username=session.get("username"),
        role=session.get("role"),
        general_topics=general_topics,
        resmi_konular=resmi_konular,
        aktif_adminler=aktif_adminler,
        topPopularTopics=topPopularTopics
    )


# ---------------------------
# KAYIT
# ---------------------------
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if not username or not password:
        flash("Kullanıcı adı ve şifre gerekli.", "error")
        return redirect(url_for("home"))

    users = load_users()

    if username in users:
        flash("Bu kullanıcı adı zaten alınmış!", "error")
        return redirect(url_for("home"))

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    users[username] = {
        "email": email or "",
        "password": hashed_pw.decode("utf-8"),
        "role": "uye"
    }

    save_users(users)
    flash("Kayıt başarılı! Şimdi giriş yapabilirsin.", "success")
    return redirect(url_for("home"))


# ---------------------------
# GİRİŞ
# ---------------------------
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    users = load_users()

    if username not in users:
        flash("Kullanıcı bulunamadı!", "error")
        return redirect(url_for("home"))

    stored_hash = users[username]["password"].encode("utf-8")

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash):
        session["username"] = username
        session["role"] = users[username]["role"]
        flash("Giriş başarılı!", "success")
        return redirect(url_for('main'))
    else:
        flash("Hatalı şifre!", "error")
        return redirect(url_for("home"))


# ---------------------------
# ÇIKIŞ
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptın!", "success")
    return redirect(url_for("home"))


# ---------------------------
# ROL AYARLAMA
# ---------------------------
@app.route("/setrole", methods=["GET", "POST"])
def setrole():
    if "role" not in session or session["role"] != "admin":
        flash("Bu sayfaya erişim iznin yok!", "error")
        return redirect(url_for("main"))

    users = load_users()

    if request.method == "POST":
        username = request.form.get("username")
        role = request.form.get("role")
        if username in users:
            users[username]["role"] = role
            save_users(users)
            flash(f"{username} adlı kullanıcının rolü '{role}' olarak güncellendi!", "success")
        else:
            flash("Kullanıcı bulunamadı!", "error")
        return redirect(url_for("setrole"))

    return render_template("setrole.html", users=users)


# ---------------------------
# KONU SİSTEMİ
# ---------------------------
@app.route("/create-topic", methods=["GET", "POST"])
def create_topic():
    if "username" not in session:
        flash("Konu oluşturmak için giriş yapmalısın!", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        if not title or not content:
            flash("Başlık ve içerik gerekli.", "error")
            return redirect(url_for("create_topic"))

        with open(TOPIC_FILE, "r", encoding="utf-8") as f:
            topics = json.load(f)

        new_id = (topics[-1]["id"] + 1) if topics else 1

        new_topic = {
            "id": new_id,
            "title": title,
            "content": content,
            "author": session["username"],
            "date": datetime.now().strftime("%d.%m.%y"),
            "visit_count": 0
        }

        topics.append(new_topic)

        with open(TOPIC_FILE, "w", encoding="utf-8") as f:
            json.dump(topics, f, indent=4, ensure_ascii=False)

        flash("Konu başarıyla oluşturuldu!", "success")
        return redirect(url_for("main"))

    return render_template("createk.html")


@app.route("/topic/<int:topic_id>")
def topic_view(topic_id):
    if "username" not in session:
        flash("Konuyu görmek için giriş yapmalısın!", "error")
        return redirect(url_for("home"))

    with open(TOPIC_FILE, "r", encoding="utf-8") as f:
        topics = json.load(f)

    topic = next((t for t in topics if t["id"] == topic_id), None)

    if topic is None:
        flash("Konu bulunamadı!", "error")
        return redirect(url_for("main"))

    topic["visit_count"] = topic.get("visit_count", 0) + 1

    with open(TOPIC_FILE, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=4, ensure_ascii=False)

    return render_template(
        "topic.html",
        topic=topic,
        username=session.get("username"),
        role=session.get("role")
    )


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
