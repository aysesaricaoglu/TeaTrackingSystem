import logging
from werkzeug.security import check_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    # handlers= [logging.StreamHandler(),
    #          logging.FileHandler("app.log")]
)
import os
import re
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from flask import Flask, render_template, url_for, redirect, request, session, jsonify
from datetime import datetime, timedelta

from database import (
    create_connection,
    create_table,
    evaluate_pending_applications,
    get_pending_registrations,
    get_pending_registrations,
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
    delete_expert,
    delete_farmer,
    search_farmers,
    search_experts,
    search_deliveries,
    change_password,
    get_delivery_by_farmer_id,
    search_my_deliveries_by_delivery_date,
    add_registration,
    evaluate_pending_applications,
)

# logging.basicConfig(filename='myapp.log', level=logging.INFO)

# logger = logging.getLogger(__name__)
app = Flask(__name__)  # uygulamayı oluşturdum
app.secret_key = "tea_tracking_secret_key"  # session için gizli anahtar
print("Connected to database successfully.")
create_table()  # Program açılırken tabloları oluştur.


# show_tables()  # Program açılırken tabloları göster.
# add_test_farmers()#mutlaka yorum satırına çevir!!!
def validate_search_filters(filters):

    # Name
    if "name" in filters:

        value = filters["name"].strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        if not value.replace(" ", "").isalpha():
            raise ValueError("Name can contain only letters.")

    # Surname
    if "surname" in filters:

        value = filters["surname"].strip()

        if not value:
            raise ValueError("Surname cannot be empty.")

        if not value.replace(" ", "").isalpha():
            raise ValueError("Surname can contain only letters.")

    # TC Number
    if "tc" in filters:

        value = filters["tc"].strip()

        if not value:
            raise ValueError("TC Number cannot be empty.")

        if not value.isdigit():
            raise ValueError("TC Number can contain only digits.")

        if len(value) != 11:
            raise ValueError("TC Number must contain exactly 11 digits.")

    # City
    if "city" in filters:

        value = filters["city"].strip()

        if not value:
            raise ValueError("City cannot be empty.")

        if not value.replace(" ", "").isalpha():
            raise ValueError("City can contain only letters.")

    # District
    if "district" in filters:

        value = filters["district"].strip()

        if not value:
            raise ValueError("District cannot be empty.")

        if not value.replace(" ", "").isalpha():
            raise ValueError("District can contain only letters.")

    # Village
    if "village" in filters:

        value = filters["village"].strip()

        if not value:
            raise ValueError("Village cannot be empty.")

        if not value.replace(" ", "").isalpha():
            raise ValueError("Village can contain only letters.")

    # Phone
    if "phone" in filters:

        value = filters["phone"].strip()

        if not value:
            raise ValueError("Phone number cannot be empty.")

        if not value.isdigit():
            raise ValueError("Phone number can contain only digits.")

        if len(value) < 10 or len(value) > 11:
            raise ValueError("Phone number must contain 10 or 11 digits.")


@app.route("/", methods=["GET", "POST"])
def home():

    print("Method:", request.method, flush=True)  #

    if request.method == "POST":  # bunu da silebilirim

        tc = request.form.get("tc")
        password = request.form.get("password")

        user = get_user_by_tc(tc)

        if user is None:
            return render_template("login.html", error="User not found")

        else:
            # şifreyi kontol ettiğim kısım
            if check_password_hash(user[2], password):
                print("Login successful", flush=True)
                session["user_id"] = user[0]
                session["tc_no"] = user[1]
                session["role"] = user[3]
                session["first_name"] = user[4]
                session["last_name"] = user[5]
                session["login_time"] = datetime.now().timestamp()

                return redirect(url_for("dashboard"))

            else:

                print("Incorrect password", flush=True)

                return render_template("login.html", error="Incorrect password")

    return render_template("login.html")


@app.route("/delete-delivery/<int:delivery_id>", methods=["POST"])
def delete_delivery_route(delivery_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") not in ["admin"]:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    try:
        delete_delivery(delivery_id)
        return jsonify({"success": True, "message": "Delivery deleted successfully!"})
    except Exception as e:
        app.logger.exception("delete_delivery failed")
        return jsonify({"success": False, "message": f"Sunucu hatası: {str(e)}"}), 500


@app.route("/deliveries")
def all_deliveries():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] not in ["admin", "expert"]:
        return redirect(url_for("dashboard"))

    deliveries = get_all_deliveries_full()

    return render_template("delivery_records.html", deliveries=deliveries)


@app.route("/api/deliveries/search", methods=["POST"])
def search_deliveries_api():

    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") not in ["admin", "expert"]:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    try:
        data = request.get_json()

        filters = data.get("filters", {})

        deliveries = search_deliveries(filters)

        return jsonify({"success": True, "deliveries": deliveries}), 200
    except Exception as e:
        app.logger.exception("search_deliveries_api failed")
        return jsonify({"success": False, "message": str(e)}), 500


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
    return render_template("new_delivery.html")


@app.route("/api/new_delivery", methods=["POST"])
def create_delivery():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    if session["role"] not in ["admin", "expert"]:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    data = request.get_json()
    farmer_tc = data.get("farmer_tc")

    user = get_user_by_tc(farmer_tc)

    if user is None:
        return jsonify({"success": False, "message": "Farmer not found"}), 404

    user_id = user[0]
    farmer = get_farmer_by_user_id(user_id)
    if farmer is None:
        return jsonify({"success": False, "message": "farmer not found!"}), 404

    farmer_id = farmer[0]

    gross_weight = float(data.get("gross_weight"))
    is_rainy = int(data.get("is_rainy"))
    if is_rainy == 1:

        net_weight = gross_weight * 0.9
    else:
        net_weight = gross_weight

    payment_option = data.get("payment_option")
    delivery_date = data.get("delivery_date")
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
    return jsonify({"success": True, "message": "delivery added successfully!"})


# ADMİN - FARMER#


@app.route("/admin/farmers")
def farmer_management():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session["role"] != "admin":
        return redirect(url_for("dashboard"))

    return render_template(
        "farmer_management.html",
    )


@app.route("/api/farmers/search", methods=["POST"])
def search_farmers_api():

    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Forbidden"}), 403

    try:
        data = request.get_json()

        filters = data.get("filters", {})
        farmers = search_farmers(filters)
        return jsonify({"success": True, "farmers": farmers}), 200

    except Exception as e:
        app.logger.exception("search_farmers_api failed")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/farmers/add", methods=["GET", "POST"])
def add_farmer_route():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    return render_template("add_farmer.html")


@app.route("/api/farmers/add", methods=["POST"])
def add_farmer_api():

    if "user_id" not in session:
        return {"success": False, "message": "Unauthorized"}, 401

    if session.get("role") != "admin":
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
        village,
    )

    if not farmer_added:
        return (
            jsonify({"success": False, "message": "Farmer could not be created."}),
            400,
        )

    return jsonify({"success": True, "message": "Farmer added successfully."})


# ADMIN - EXPERT#


@app.route("/admin/experts")
def expert_management():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    search = request.args.get("search", "")

    experts = get_all_experts(search)

    return render_template(
        "expert_management.html",
    )


@app.route("/api/experts/search", methods=["POST"])
def search_experts_api():

    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Forbidden"}), 403
    try:
        data = request.get_json()

        filters = data.get("filters", {})
        experts = search_experts(filters)
        return jsonify({"success": True, "experts": experts}), 200

    except Exception as e:
        app.logger.exception("search_experts_api failed")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/admin/experts/add", methods=["GET", "POST"])
def add_expert_route():
    if "user_id" not in session:
        return redirect(url_for("home"))
    if session.get("role") != "admin":
        return redirect(url_for("dashboard"))
    return render_template("add_expert.html")


@app.route("/api/experts/add", methods=["POST"])
def add_expert_api():
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Forbidden"}), 403

    data = request.get_json()
    tc_no = data.get("tc_no")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    expert_added = add_expert(tc_no, password, "expert", first_name, last_name)
    if not expert_added:
        return jsonify({"success": False, "message": "Expert could not be added"}), 400

    return jsonify({"success": True, "message": "Expert added succesfully!!!"})


@app.route("/api/experts/delete/<int:expert_id>", methods=["POST"])
def delete_expert_api(expert_id):
    # Güvenlik ve yetki kontrolleri
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "Forbidden"}), 403

    # database.py'deki silme fonksiyonunu çağırıyoruz
    # expert_id adres çubuğundan (<int:expert_id>) otomatik olarak geliyor
    delete_success = delete_expert(expert_id)

    if delete_success:
        return jsonify({"success": True, "message": "Expert deleted succesfully!"})
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Error occured when expert's deleting process.",
                }
            ),
            400,
        )


@app.route("/admin/farmers/delete/<int:farmer_id>", methods=["POST"])
def delete_farmer_api(farmer_id):
    if "user_id" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    if session.get("role") != "admin":
        return jsonify({"success": False, "message": "forbidden"}), 403

    delete_success = delete_farmer(farmer_id)

    if delete_success:
        return jsonify({"success": True, "message": "Farmer deleted succesfully!"})
    else:
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Error occured when expert's deleting process.",
                }
            ),
            400,
        )


# 1. HTML Sayfasını Ekrana Getiren Rota (GET)
@app.route("/change-password", methods=["GET"])
def change_password_page():
    return render_template("change_password.html")


# 2. Butona Basınca Arka Planda Şifreyi Güncelleyen API (POST)
@app.route("/api/change-password", methods=["POST"])
def api_change_password():

    if "tc_no" not in session:
        return jsonify({"message": "Username not found. Please log in."}), 401

    data = request.get_json()
    tc_no = data.get("tc_no")
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if tc_no != session.get("tc_no"):
        return jsonify({"message": "TC number does not match your session."}), 403

    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT password FROM users WHERE tc_no = ?", (tc_no,))
    row = cursor.fetchone()
    cursor.close()
    connection.close()

    if row is None:
        return jsonify({"message": "User not found."}), 404

    if not check_password_hash(row[0], current_password):
        return jsonify({"message": "Current password is wrong."}), 401

    change_password(tc_no, new_password)

    return jsonify({"message": "Password changed successfully."}), 200


@app.route("/farmer/my-deliveries")
def my_deliveries():
    if "user_id" not in session or session.get("role") != "farmer":
        return redirect(url_for("home"))

    farmer_id = session["user_id"]
    delivery_records = get_delivery_by_farmer_id(farmer_id)

    return render_template("my_deliveries.html", deliveries=delivery_records)


@app.route("/api/farmer/my-deliveries/search", methods=["POST"])
def search_deliveries_by_delivery_date_api():
    if "user_id" not in session or session.get("role") != "farmer":
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    try:
        data = request.get_json()
        filters = data.get("filters", {})
        deliveries = search_my_deliveries_by_delivery_date(
            session["user_id"], filters.get("start_date"), filters.get("end_date")
        )
        return jsonify({"success": True, "deliveries": deliveries}), 200
    except Exception as e:
        app.logger.exception("search_deliveries_by_delivery_date_api failed")
        return jsonify({"success": False, "message": str(e)}), 500


@app.before_request  # her requestten önce bu kodu çalıştır
def check_session_timeout():

    if "user_id" not in session:
        return

    role = session.get("role")

    # Farmer: süresiz
    if role == "farmer":
        return

    login_time = session.get("login_time")

    if not login_time:
        session.clear()
        return redirect(url_for("home"))

    elapsed = datetime.now().timestamp() - login_time

    if elapsed > 1800:
        session.clear()
        return redirect(url_for("home"))


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


@app.route("/registration", methods=["GET"])
def registration_page():
    return render_template("registration.html")

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route("/registration", methods=["POST"])
def registration_page_api():
    if "user_id" in session:
        return jsonify({"success": False, "message": "You are already logged in."}), 400

    if "application_submitted" in session:
        return jsonify({"success": False, "message": "You have already submitted an application."}), 400

    tc_no = request.form.get("tc_no")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm_password")
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    city = request.form.get("city")
    district = request.form.get("district")
    phone_number = request.form.get("phone_number")
    village = request.form.get("village")

    if not all([tc_no, password, confirm_password, first_name, last_name, city, district, phone_number, village]):
        return jsonify({"success": False, "message": "Please fill in all fields."}), 400

    if password != confirm_password:
        return jsonify({"success": False, "message": "Passwords do not match."}), 400

    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters."}), 400

    if not re.fullmatch(r"\d{11}", tc_no):
        return jsonify({"success": False, "message": "TC Number must be exactly 11 digits."}), 400

    land_register_file = request.files.get("land_register")

    if not land_register_file or land_register_file.filename == "":
        return jsonify({"success": False, "message": "Land register document is required."}), 400

    if not allowed_file(land_register_file.filename):
        return jsonify({"success": False, "message": "Invalid file type. Only PDF, JPG, PNG allowed."}), 400
    

    land_register_file.seek(0, os.SEEK_END)
    file_size = land_register_file.tell()
    land_register_file.seek(0)
    if file_size > MAX_FILE_SIZE:
        return jsonify({"success": False, "message": "File exceeds 5MB limit."}), 400

    filename = secure_filename(land_register_file.filename)
    os.makedirs("uploads", exist_ok=True)
    land_register_file.save(f"uploads/{filename}")

    registration_added = add_registration(
        tc_no,
        first_name,
        last_name,
        city,
        district,
        phone_number,
        village,
        generate_password_hash(password),
        filename
    )

    if not registration_added:
        return jsonify({"success": False, "message": "This TC Number is already registered."}), 400

    session["application_submitted"] = True

    return jsonify({"success": True, "message": "Application submitted successfully."}), 200


@app.route("/api/admin/pending-registrations", methods=["GET"])
def pending_registrations_api():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    registrations = get_pending_registrations()
    return jsonify({
        "success": True,
        "count": len(registrations),
        "registrations": registrations
    }), 200

@app.route("/admin/evaluate-applications", methods=["POST"])
def evaluate_applications_route():
    if "user_id" not in session or session.get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    approved_count, rejected_count = evaluate_pending_applications()
    return jsonify({
        "success": True,
        "message": f"{approved_count} application(s) approved, {rejected_count} rejected."
    }), 200



if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=80, debug=True
    )  # Flask uygulamasını başlatır ve debug modunu açar(koddaki değişiklikleri otomatik olarak algılar ve uygulamayı yeniden başlatır)
