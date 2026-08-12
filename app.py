import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("app.log")]
)

logger = logging.getLogger(__name__)
from flask import Flask, render_template, url_for, redirect, request, session,jsonify

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
    get_all_deliveries_full,
    get_all_farmers,
    get_all_experts,
    add_expert,
    delete_expert
)

# logging.basicConfig(filename='myapp.log', level=logging.INFO)

# logger = logging.getLogger(__name__)


app = Flask(__name__)  # uygulamayı oluşturdum
app.secret_key = "tea_tracking_secret_key"  # session için gizli anahtar
print("Connected to database successfully.")
create_table()  # Program açılırken tabloları oluştur.
# show_tables()  # Program açılırken tabloları göster.

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


#ADMİN - FARMER#

@app.route("/admin/farmers")
def farmer_management():

    if "user_id" not in session:
        return redirect(url_for("home"))
    if session ["role"] != "admin":
        return redirect(url_for("dashboard"))

    search= request.args.get("search","")

    farmers = get_all_farmers(search)

    return render_template (
        "farmer_management.html",
        farmers=farmers,
        search=search

    )
@app.route("/admin/farmers/add", methods=["GET", "POST"])
def add_farmer_route():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    return render_template("add_farmer.html")

@app.route("/api/farmers/add", methods=["POST"])
def add_farmer_api():

    if "user_id" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    if session["role"] != "admin":
        return {"success": False, "message": "Forbidden"}, 403

    # JavaScript fetch() tarafından gönderilen JSON verisini alıyoruz
    data = request.get_json()

    tc_no = data.get("tc_no")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    city = data.get("city")
    district = data.get("district")
    phone_number = data.get("phone_number")
    village = data.get("village")

    # Farmer bilgilerini farmers tablosuna ekliyoruz
    farmer_added = add_farmer(
        tc_no,
        password,
        "farmer",
        first_name,
        last_name,
        city,
        district,
        phone_number,
        village
    )

    if not farmer_added:
        return jsonify({
            "success": False,
            "message": "Farmer could not be created."
        }), 400

    logger.info(
        f"Farmer added: {first_name} {last_name}, TC: {tc_no}"
    )

    return jsonify( {
        "success": True,
        "message": "Farmer added successfully."
    })


#ADMIN - EXPERT#
@app.route("/admin/experts")
def expert_management():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    search = request.args.get("search", "")

    experts = get_all_experts(search)

    return render_template(
        "expert_management.html",
        experts=experts,
        search=search
    )
@app.route("/admin/experts/add",methods=["GET","POST"])

def add_expert_route():
    if "user_id" not in session:
        return redirect( url_for ("home"))
    if session["role"] != "admin" :
        return redirect(url_for("dashboard"))
    return render_template("add_expert.html")

@app.route("/api/experts/add",methods=["POST"])
def add_expert_api():
    if "user_id" not in session:
        return jsonify({"success":False, "message":"Unauthorized"}),401
    
    if session["role"]!= "admin":
        return jsonify({"success":False, "message": "Forbidden"}),403

    data= request.get_json()
    tc_no = data.get("tc_no")
    password= data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    expert_added = add_expert(
        tc_no,
        password,
        "expert",
        first_name,
        last_name
    )
    if not expert_added:
        return jsonify({
            "success":False,
            "message": "Expert could not be added"
        }),400
    logger.info(
        f"Expert added:{first_name} {last_name},TC: {tc_no}"
    )

    return jsonify( {
        "success":True,
        "message": "Expert added succesfully!!!"
    })




@app.route("/api/experts/delete/<int:expert_id>", methods=["POST"])
def delete_expert_api(expert_id):
    # Güvenlik ve yetki kontrolleri
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    if session["role"] != "admin":
        return jsonify({"success": False, "message": "Forbidden"}), 403

    # database.py'deki silme fonksiyonunu çağırıyoruz
    # expert_id adres çubuğundan (<int:expert_id>) otomatik olarak geliyor
    delete_success = delete_expert(expert_id)

    if delete_success:
        return jsonify({"success": True, "message": "Expert deleted succesfully!"})
    else:
        return jsonify({"success": False, "message": "Error occured when exper's deleteing process."}), 400


@app.route("/ai_assistant")
def ai_assistant():
    return render_template("ai_assistant.html")

@app.route("/statistics")
def statistics():
    return render_template("statistics.html")

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
