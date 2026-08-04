from flask import Flask,render_template, request
from database import create_connection, create_table, show_tables

connection = create_connection()

app = Flask(__name__) #uygulamayı oluşturdum
print("Connected to database successfully.")
create_table()   # Program açılırken tabloları oluştur.
show_tables()#bunu sonradan silmeliyim


@app.route("/", methods=["GET", "POST"])
def home():

    print("Method:", request.method, flush=True)

    if request.method == "POST":

        print("POST came", flush=True)

        tc = request.form.get("tc")
        password = request.form.get("password")

        print(tc, flush=True)
        print(password, flush=True)

    return render_template("login.html")

@app.route("/farmer")
def farmer_dashboard():
    return render_template("farmer_dashboard.html")

@app.route("/expert")
def expert_dashboard():
    return render_template("expert_dashboard.html")

if __name__ == "__main__":# eğer bu dosyayı doğrudan çalıştırıyorsam aşağıdaki kodu çalıştır demekmiş
    app.run(debug=True)# Flask uygulamasını başlatır ve debug modunu açar(koddaki değişiklikleri otomatik olarak algılar ve uygulamayı yeniden başlatır)
