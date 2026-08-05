from flask import Flask, render_template,url_for, redirect,request
from database import create_table, show_tables, get_user_by_tc,add_user

app = Flask(__name__)  # uygulamayı oluşturdum
print("Connected to database successfully.")
create_table()  # Program açılırken tabloları oluştur.

"""add_user(
    "11111111111",
    "123456",
    "admin",
    "Ayşe",
    "Sarıcaoğlu"
)"""
add_user(
    "22222222222",
    "123456",
    "farmer",
    "Ali",
    "Yılmaz"
)
add_user(
    "33333333333",
    "123456",
    "expert",
    "Mehmet",
    "Demir"
)

show_tables()  # bunu sonradan silmeliyim


@app.route("/", methods=["GET", "POST"])
def home():

    print("Method:", request.method, flush=True)  #

    if request.method == "POST":  # bunu da silebilirim

        print("POST came", flush=True)  # bu da gereksiz

        tc = request.form.get("tc")
        password = request.form.get("password")

        user = get_user_by_tc(tc)

        if user is None:
            return render_template(
                "login.html",
                error="User not found"
            )

        else:

            if password == user[2]:

                print("Login successful", flush=True)

                role = user[3]

                if role == "farmer":
                    return redirect(url_for("farmer_dashboard"))

                elif role == "expert":
                    return redirect(url_for("expert_dashboard"))

                elif role == "admin":
                    return redirect(url_for("admin_dashboard"))

                else:
                    return render_template(
                        "login.html",
                        error="Invalid role"
                    )

            else:

                print("Incorrect password", flush=True)

                return render_template(
                    "login.html",
                    error="Incorrect password"
                )

    return render_template("login.html")


@app.route("/farmer")
def farmer_dashboard():
    return render_template("farmer_dashboard.html")


@app.route("/expert")
def expert_dashboard():
    return render_template("expert_dashboard.html")

@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


if __name__ == "__main__":  # eğer bu dosyayı doğrudan çalıştırıyorsam aşağıdaki kodu çalıştır demekmiş
    app.run(debug=True)  # Flask uygulamasını başlatır ve debug modunu açar(koddaki değişiklikleri otomatik olarak algılar ve uygulamayı yeniden başlatır)