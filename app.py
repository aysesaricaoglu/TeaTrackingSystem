import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("app.log")]
)

logger = logging.getLogger(__name__)
from flask import Flask, render_template, url_for, redirect, request, session

from database import (
    create_table,
    show_tables,
    get_user_by_tc,
    add_user,
    get_all_users,
    add_delivery,
    get_all_deliveries,
    get_farmer_by_user_id,
    add_farmer,
    delete_delivery,
    get_all_deliveries_full
)

# logging.basicConfig(filename='myapp.log', level=logging.INFO)

# logger = logging.getLogger(__name__)


app = Flask(__name__)  # uygulamayı oluşturdum
app.secret_key = "tea_tracking_secret_key"  # session için gizli anahtar
print("Connected to database successfully.")
create_table()  # Program açılırken tabloları oluştur.
# show_tables()  # Program açılırken tabloları göster.
"""add_user(
    "1",
    "1",
    "admin",
    "Ayşe",
    "Sarıcaoğlu"
)
add_user(
    "2",
    "2",
    "farmer",
    "Ali",
    "Yılmaz"
)
add_user(
    "3",
    "3",
    "expert",
    "Mehmet",
    "Demir"
)
add_user(
    "4",
    "4",
    "admin",
    "Hakan",
    "Özcan"
)
add_user(
    "5",
    "5",
    "expert",
    "Ayşe",
    "Yılmaz"
)
add_farmer(
    "2",
    "Ali",
    "Yılmaz",
    "Trabzon",
    "Sürmene",
    "222 222 22 22",
    "Dereli",
)
add_user(
    "46303345424",
    "5",
    "farmer",
    "Ayşe",
    "zattiri"
)"""
add_farmer(
    "8",
    "Ayşe",
    "zattiri",
    "Trabzon",
    "Of",
    "222 222 22 22",
    "halman")
@app.route("/", methods=["GET", "POST"])
def home():

    print("Method:", request.method, flush=True)  #

    if request.method == "POST":  # bunu da silebilirim

        print("POST came", flush=True)  # bu da gereksiz

        tc = request.form.get("tc")
        password = request.form.get("password")

        user = get_user_by_tc(tc)

        if user is None:
            return render_template("login.html", error="User not found")

        else:

            if password == user[2]:

                print("Login successful", flush=True)
                session["user_id"] = user[0]
                session["tc_no"] = user[1]
                session["role"] = user[3]
                session["first_name"] = user[4]
                session["last_name"] = user[5]

                return redirect(url_for("dashboard"))

              

            else:

                print("Incorrect password", flush=True)

                return render_template("login.html", error="Incorrect password")

    return render_template("login.html")


# @app.route("/farmer")
# def farmer_dashboard():
#     if "user_id" not in session:
#         return redirect(url_for("home"))
#     if session["role"] != "farmer":
#         return redirect(url_for("home"))
#     return render_template("farmer_dashboard.html")


# @app.route("/expert", methods=["GET", "POST"])
# def expert_dashboard():
#     print(request.method)
#     if "user_id" not in session:
#         return redirect(url_for("home"))
#     if session["role"] != "expert":
#         return redirect(url_for("home"))
#     if request.method == "POST":
#         # print("POST request received in expert_dashboard", flush=True)
#         logger.info("POST request received in expert_dashboard")

#         # burdan aşağıya getleri yazdım
#         farmer_tc = request.form.get("farmer_tc")
#         user = get_user_by_tc(farmer_tc)
#         if user is None:
#             return "farmer not found!"  # BU SATIR ÇALIŞACAK MI EMİN DEĞİLİM
#         user_id = user[0]

#         farmer= get_farmer_by_user_id(user_id)

#         if farmer is None:
#             return"Farmer not found"
#         farmer_id = farmer[0]

#         delivery_date = request.form.get("delivery_date")
#         gross_weight = float(request.form.get("gross_weight"))
#         is_rainy = int(request.form.get("is_rainy"))

#         if is_rainy == 1:
#             net_weight = gross_weight * 0.9  # %10 kesinti
#         else:
#             net_weight = gross_weight  # yağmur yoksa kesinti yok
#         payment_option = request.form.get("payment_option")
#         expert_id = session["user_id"]

#         print("ADD_DELIVERY ÇAĞRILIYOR")
#         add_delivery(
#             farmer_id,
#             expert_id,
#             delivery_date,
#             gross_weight,
#             net_weight,
#             is_rainy,
#             payment_option,
#         )

#     deliveries= get_all_deliveries()

#     return render_template("dashboard.html",
#                            deliveries=deliveries)


# @app.route("/admin")
# def admin_dashboard():
#     if "user_id" not in session:
#         return redirect(url_for("home"))
#     if session["role"] != "admin":
#         return redirect(url_for("home"))
#     users = get_all_users()
#     # print(users, flush=True) # kullanıcıları yazdırmak için ekledim, sonradan silebilirim
#     # logger.info("ayse")

#     return render_template("admin_dashboard.html", users=users)



@app.route("/delete-delivery/<int:delivery_id>", methods=["POST"])
def delete_delivery_route(delivery_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] not in ["admin"]:
        return redirect(url_for("dashboard"))

    delete_delivery(delivery_id)

    return redirect(url_for("all_deliveries"))



@app.route("/deliveries")
def all_deliveries():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] not in ["admin", "expert"]:
        return redirect(url_for("dashboard"))

    deliveries = get_all_deliveries_full()

    return render_template(
        "all_deliveries.html",
        deliveries=deliveries
    )

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("home"))

    return render_template("dashboard.html")

@app.route("/new-delivery", methods=["GET", "POST"])
def new_delivery():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] not in ["admin", "expert"]:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        farmer_tc = request.form.get("farmer_tc")

        user = get_user_by_tc(farmer_tc)

        if user is None:
            return "Farmer not found!"

        user_id = user[0]

        farmer = get_farmer_by_user_id(user_id)

        if farmer is None:
            return "Farmer not found!"

        farmer_id = farmer[0]

        delivery_date = request.form.get("delivery_date")
        gross_weight = float(request.form.get("gross_weight"))
        is_rainy = int(request.form.get("is_rainy"))

        if is_rainy == 1:
            net_weight = gross_weight * 0.9
        else:
            net_weight = gross_weight

        payment_option = request.form.get("payment_option")
        expert_id = session["user_id"]

        add_delivery(
            farmer_id,
            expert_id,
            delivery_date,
            gross_weight,
            net_weight,
            is_rainy,
            payment_option,
        )

        return redirect(url_for("all_deliveries"))

    return render_template("new_delivery.html")



@app.route("/logout")
def logout():
    session.clear()  # session da tuutuğum username role falan her şeyi siliyoum
    return redirect(url_for("home"))  # login sayfasına yönlendir


if (
    __name__ == "__main__"
):  # eğer bu dosyayı doğrudan çalıştırıyorsam aşağıdaki kodu çalıştır demekmiş
    app.run(
        debug=True
    )  # Flask uygulamasını başlatır ve debug modunu açar(koddaki değişiklikleri otomatik olarak algılar ve uygulamayı yeniden başlatır)
