from flask import Flask,render_template
from database import create_connection

connection = create_connection()

app = Flask(__name__) #uygulamayı oluşturdum
print("Connected to database successfully.")

@app.route("/") 
def home():
    return render_template("login.html") # flaskin kuralıymış render_template dediğimde otomatik templates klasörüne bakıyormuş ki ben de login pageimi buraya yazdım.
if __name__ == "__main__":# eğer bu dosyayı doğrudan çalıştırıyorsam aşağıdaki kodu çalıştır demekmiş
    app.run(debug=True)# Flask uygulamasını başlatır ve debug modunu açar(koddaki değişiklikleri otomatik olarak algılar ve uygulamayı yeniden başlatır)


