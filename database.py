import sqlite3
import logging
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime, timedelta

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[logging.StreamHandler(),
#               logging.FileHandler("database.log")
# ],
# )
# logger = logging.getLogger(__name__)
DATABASE_NAME = "tea.db"

def normalize_search_text(text):
    if text is None:
        return ""

    text = str(text).strip()

    replacements = str.maketrans({
        "ç": "c",
        "Ç": "c",
        "ğ": "g",
        "Ğ": "g",
        "ı": "i",
        "I": "i",
        "İ": "i",
        "i": "i",
        "ö": "o",
        "Ö": "o",
        "ş": "s",
        "Ş": "s",
        "ü": "u",
        "Ü": "u"
    })

    return text.translate(replacements).casefold()

def create_connection():
    connection = sqlite3.connect(DATABASE_NAME)

    connection.create_function(
            "normalize_text",
            1,
            normalize_search_text
    )

    return connection


def create_table():
    connection = create_connection()
    cursor = (
        connection.cursor()
    )  # garson gibi düşünebiliriz. garson siparişleri alır ve mutfağa iletir.
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         tc_no TEXT UNIQUE NOT NULL,
         password TEXT NOT NULL,
         role TEXT NOT NULL,
         first_name TEXT NOT NULL,
         last_name TEXT NOT NULL,
         is_active INTEGER DEFAULT 1
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS tea_delivers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    expert_id INTEGER NOT NULL,
    delivery_date TEXT NOT NULL,
    gross_weight REAL NOT NULL,
    net_weight REAL NOT NULL,
    is_rainy INTEGER NOT NULL,
    payment_option TEXT NOT NULL,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (expert_id) REFERENCES users(id)

    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS farmers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    city TEXT NOT NULL,
    district TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    village TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS turkiye_production(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER ,
    month TEXT,
    production REAL)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id INTEGER NOT NULL,
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (delivery_id) REFERENCES tea_delivers(id))""")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
    except:
        pass # Hata verirse (kolon zaten eklenmişse) umursama, geç.

    try:
        cursor.execute("ALTER TABLE farmers ADD COLUMN is_active INTEGER DEFAULT 1")
    except:
        pass # Hata verirse umursama, geç
    connection.commit()  # commit işlemi veritabanına değişiklikleri kaydeder. yani garson mutfağa ilettiği siparişin tamamlandığını ve artık mutfakta hazır olduğunu bildirir.
    connection.close()


def show_tables():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()

    print("Tables in Database:")
    for table in tables:
        print(table[0])
    connection.close()


def get_user_by_tc(tc_no):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE tc_no = ?", (tc_no,))
    user = (
        cursor.fetchone()
    )  # fetchone() metodu, sorgu sonucunda dönen ilk satırı alır ve bir tuple olarak döndürür. Eğer sorgu sonucunda hiç satır dönmezse None döner.
    connection.close()
    return user


def add_user(tc_no, password, role, first_name, last_name):

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE tc_no = ?", (tc_no,)
    )  # kullanıcıyı eklemeden önce veritabanında aynı tc_no'ya sahip bir kullanıcı olup olmadığını kontrol ediyoruz.
    existing_user = (
        cursor.fetchone()
    )  # fetchone() metodu, sorgu sonucunda dönen ilk satırı alır ve bir tuple olarak döndürür. Eğer sorgu sonucunda hiç satır dönmezse None döner.
    if existing_user:
        connection.close()
        return False
    hashed_password = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (tc_no, password, role, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
        (tc_no, hashed_password, role, first_name, last_name),
    )
    connection.commit()
    connection.close()
    return True


def get_all_users():
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    connection.close()
    return users




def get_all_deliveries():#bunu şu anda kullanmıyorum ama dashboarda ekleyeceğim
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            tea_delivers.id,
            farmers.first_name,
            farmers.last_name,
            users.first_name,
            users.last_name,
            tea_delivers.delivery_date,
            tea_delivers.gross_weight,
            tea_delivers.net_weight,
            tea_delivers.is_rainy,
            tea_delivers.payment_option
        FROM tea_delivers
        JOIN farmers ON tea_delivers.farmer_id = farmers.id
        JOIN users ON tea_delivers.expert_id = users.id
        ORDER BY tea_delivers.id DESC LIMIT 5
    """)

    deliveries = cursor.fetchall()

    connection.close()

    return deliveries
def search_deliveries(filters):
    connection = create_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            tea_delivers.id,
            farmers.first_name ||' '|| farmers.last_name,
            experts.first_name||' '||experts.last_name,
            tea_delivers.delivery_date,
            tea_delivers.gross_weight,
            tea_delivers.net_weight,
            tea_delivers.is_rainy,
            tea_delivers.payment_option
        FROM tea_delivers

        JOIN farmers
            ON tea_delivers.farmer_id = farmers.id

        JOIN users AS experts
            ON tea_delivers.expert_id = experts.id

        WHERE 1 = 1
    """

    parameters = []

    if filters.get("farmer_name"):
        query += """
            AND normalize_text(farmers.first_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['farmer_name'])}%"
        )

    if filters.get("farmer_surname"):
        query += """
            AND normalize_text(farmers.last_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['farmer_surname'])}%"
        )

    if filters.get("expert_name"):
        query += """
            AND normalize_text(experts.first_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['expert_name'])}%"
        )

    if filters.get("expert_surname"):
        query += """
            AND normalize_text(experts.last_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['expert_surname'])}%"
        )

    if filters.get("farmer_tc"):
        query += """
            AND farmers.user_id IN (
                SELECT id
                FROM users
                WHERE tc_no LIKE ?
            )
        """
        parameters.append(f"%{filters['farmer_tc'].strip()}%")

    if filters.get("date"):
        query += """
            AND tea_delivers.delivery_date BETWEEN ? AND ?
        """
        parameters.append(filters["delivery_start_date"])
        parameters.append(filters["delivery_end_date"])

    if filters.get("is_rainy") is not None:
        query += """
            AND tea_delivers.is_rainy = ?
        """
        parameters.append(filters["is_rainy"])

    if filters.get("payment_option"):
        query += """
            AND normalize_text(tea_delivers.payment_option) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['payment_option'])}%"
        )

    if filters.get("gross_weight"):
        query += """
            AND tea_delivers.gross_weight >= ?
        """
        parameters.append(float(filters["gross_weight"]))

    if filters.get("net_weight"):
        query += """
            AND tea_delivers.net_weight >= ?
        """
        parameters.append(float(filters["net_weight"]))

    query += """
        ORDER BY tea_delivers.id DESC
    """

    cursor.execute(query, tuple(parameters))

    deliveries = cursor.fetchall()

    connection.close()

    return deliveries

def add_delivery(
    farmer_id,
    expert_id,
    delivery_date,
    gross_weight,
    net_weight,
    is_rainy,
    payment_option,
):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(
        """INSERT INTO tea_delivers(
        farmer_id,
        expert_id,
        delivery_date,
        gross_weight,
        net_weight,
        is_rainy,
        payment_option) VALUES(?,?,?,?,?,?,?)""",
        (
            farmer_id,
            expert_id,
            delivery_date,
            gross_weight,
            net_weight,
            is_rainy,
            payment_option,
        ),
    )
    # logger.info(f"""Farmer ID:{farmer_id}
    # Expert ID: {expert_id}
    # Date: {delivery_date}
    # Gross Weight: {gross_weight}
    # Net Weight: {net_weight}
    # Rainy: {is_rainy}
    # Payment: {payment_option}""")
    connection.commit()  # yapılan değişiklikleri kaydetmek için
    connection.close()  # bağlantıyı kapatmak için

def get_farmer_by_user_id(user_id):
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            first_name,
            last_name,
            city,
            district,
            phone_number,
            village
        FROM farmers
        WHERE user_id = ?
    """, (user_id,))

    farmer = cursor.fetchone()

    connection.close()

    return farmer
def delete_delivery(delivery_id):
    connection = create_connection()
    cursor= connection.cursor()

    cursor.execute(
        "DELETE FROM tea_delivers WHERE id=?",
        (delivery_id,)
        )
    connection.commit()
    connection.close()
    logger.info(f"delivery {delivery_id} deleted.")
    return True

def get_all_deliveries_full():
    
    connection = create_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            tea_delivers.id,
            farmers.first_name || ' ' || farmers.last_name,
            experts.first_name || ' ' || experts.last_name,
            tea_delivers.delivery_date,
            tea_delivers.gross_weight,
            tea_delivers.net_weight,
            tea_delivers.is_rainy,
            tea_delivers.payment_option
        FROM tea_delivers
        JOIN farmers
            ON tea_delivers.farmer_id = farmers.id
        JOIN users AS experts
            ON tea_delivers.expert_id = experts.id
        ORDER BY tea_delivers.id DESC
    """)

    deliveries = cursor.fetchall()

    print("DELIVERIES:", deliveries)

    connection.close()

    return deliveries

def get_all_experts(search=""):
    connection = create_connection()
    cursor=connection.cursor()
    if search:
        search= f"%{search}%"# sql de '%' LIKE  kullanıldığı zaman önünde veya arkasında birşey yazabilir manasında kullanılır

        cursor.execute("""
        SELECT
          id,
          tc_no,
          first_name,
          last_name
        FROM users
        WHERE role ='expert'
         AND(
            tc_no LIKE ?
            OR first_name LIKE ?
            OR last_name LIKE ?
            is_active = 1
        )
        ORDER BY  first_name, last_name
    """,(search,search,search))#

    else:
        cursor.execute("""
            SELECT
                id,
                tc_no,
                first_name,
                last_name
            FROM users
            WHERE role ='expert'
            ORDER BY first_name , last_name
        """)
    experts =cursor.fetchall()
    connection.close()
    return experts

def delete_expert(expert_id):
    connection = create_connection()
    cursor = connection.cursor()
    try:

        cursor.execute("""
            UPDATE users
            SET is_active = 0
            WHERE id = ?
            AND role = 'expert'
        """, (expert_id,))

        connection.commit()
        return True
    except Exception as e:
        print("delete problem occured:",e)
        return False
    finally:
        connection.close()

    logger.info(f"Expert {expert_id} deleted.")

    return True

def add_expert(tc_no,password,role,first_name,last_name):
    connection =create_connection()
    cursor=connection.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE tc_no=?",(tc_no,)
    )

    existing_user= cursor.fetchone()
    if existing_user:
        connection.close()
        return False

    hashed_password = generate_password_hash(password)
    cursor.execute("""

         INSERT INTO users(
            tc_no,
            password,
            role,
            first_name,
            last_name) VALUES(?,?,?,?,?)
            """,(
                tc_no,
                hashed_password,
                role,
                first_name,
                last_name
            )
    )

    connection.commit()
    connection.close()

    return True

def search_experts(filters):
        connection =create_connection()
        cursor= connection.cursor()
        query ="""
            SELECT
                users.id,
                users.tc_no,
                users.first_name,
                users.last_name
            FROM users WHERE users.role ='expert'
        """
        parameters=[]

        if filters.get("name"):
            query += """
                AND normalize_text(users.first_name) LIKE ?
            """
            parameters.append(
                f"%{normalize_search_text(filters['name'])}%"
            )

        if filters.get("surname"):
            query += """
                AND normalize_text (users.last_name) LIKE ?
            """
            parameters.append(
                f"%{normalize_search_text(filters['surname'])}%"
            )
        if filters.get("tc"):
                query += """
                    AND users.tc_no LIKE ?
                """
                parameters.append(
                    f"%{filters['tc']}%"
                )

        query += """
        ORDER BY users.first_name, users.last_name
        """
        cursor.execute(query, tuple(parameters))

        experts = cursor.fetchall()

        connection.close()

        return experts

def search_farmers(filters):
    connection = create_connection()
    cursor = connection.cursor()

    query = """
        SELECT
            farmers.id,
            users.tc_no,
            farmers.first_name,
            farmers.last_name,
            farmers.city,
            farmers.district,
            farmers.phone_number,
            farmers.village
        FROM farmers
        JOIN users
            ON farmers.user_id = users.id
        WHERE users.role = 'farmer'
    """

    parameters = []

    if filters.get("name"):
        query += """
            AND normalize_text(farmers.first_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['name'])}%"
        )

    if filters.get("surname"):
        query += """
            AND normalize_text(farmers.last_name) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['surname'])}%"
        )

    if filters.get("tc"):
        query += """
            AND users.tc_no LIKE ?
        """
        parameters.append(
            f"%{filters['tc']}%"
        )

    if filters.get("city"):
        query += """
            AND normalize_text(farmers.city) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['city'])}%"
        )

    if filters.get("district"):
        query += """
            AND normalize_text(farmers.district) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['district'])}%"
        )

    if filters.get("village"):
        query += """
            AND normalize_text(farmers.village) LIKE ?
        """
        parameters.append(
            f"%{normalize_search_text(filters['village'])}%"
        )

    if filters.get("phone"):
        query += """
            AND farmers.phone_number LIKE ?
        """
        parameters.append(
            f"%{filters['phone']}%"
        )

    query += """
        ORDER BY farmers.first_name, farmers.last_name
    """

    cursor.execute(query, tuple(parameters))

    farmers = cursor.fetchall()

    connection.close()

    return farmers

def get_all_farmers(search=""):
    connection= create_connection()
    cursor= connection.cursor()

    if search:
        search= f"%{search}%"

        cursor.execute("""
            SELECT
                farmers.id,
                users.tc_no,
                farmers.first_name,
                farmers.last_name,
                farmers.city,
                farmers.district,
                farmers.phone_number,
                farmers.village

            FROM farmers
            JOIN users ON farmers.user_id = users.id
            WHERE
                users.role = 'farmer'
            AND(
                users.tc_no LIKE ?
                OR farmers.first_name LIKE ?
                OR farmers.last_name LIKE ?
                OR farmers.city LIKE ?
                OR farmers.district LIKE ?
                OR farmers.phone_number LIKE ?
                OR farmers.village LIKE ?

            )
        ORDER BY farmers.first_name, farmers.last_name

    """,(
            search,
            search,
            search,
            search,
            search,
            search,
            search,

))
    else:
        cursor.execute("""
            SELECT
                farmers.id,
                users.tc_no,
                farmers.first_name,
                farmers.last_name,
                farmers.city,
                farmers.district,
                farmers.phone_number,
                farmers.village
            FROM farmers
            JOIN users
                ON farmers.user_id = users.id
            WHERE users.role = 'farmer'
            ORDER BY farmers.first_name, farmers.last_name
        """)

    farmers = cursor.fetchall()

    connection.close()

    return farmers


def delete_farmer(farmer_id):
    connection = create_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT user_id FROM farmers
            WHERE id =?

        """,(farmer_id,))
        farmer =cursor.fetchone()

        if farmer is None:
            connection.close()
            return False

        user_id= farmer[0]



        cursor.execute("""

            UPDATE farmers
            SET is_active=0
            WHERE id=?
        """,(farmer_id,))

        cursor.execute("""
            UPDATE users
            SET is_active=0
            WHERE id=?
            AND role = 'farmer'
        """,(user_id,))

        connection.commit()
        return True
    except Exception as e:
        print("delete problem occured:",e)
        return False
    finally:
     connection.close()





def add_farmer(tc_no,password,role,first_name,last_name,city,district,phone_number,village):
        connection=create_connection()
        cursor= connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE tc_no =?",(tc_no,)

        )
        existing_user = cursor.fetchone()
        if existing_user:
            connection.close()
            return False

        hashed_password = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (
            tc_no,
            password,
            role,
            first_name,
            last_name) VALUES (?,?,?,?,?)
            """,(
                tc_no,
                hashed_password,
                role,
                first_name,
                last_name
            )

        )
        user_id = cursor.lastrowid# en son eklediğim şeyin id sini alıyorum

        cursor.execute("""INSERT INTO farmers(
                user_id,
                first_name,
                last_name,
                city,
                district,
                phone_number,
                village

                )VALUES (?,?,?,?,?,?,?)
                """, (

                user_id,
                first_name,
                last_name,
                city,
                district,
                phone_number,
                village
        )

    )

        connection.commit()
        connection.close()

        # logger.info(f"farmer added {first_name} {last_name} TC: {tc_no}")
    

        return True
# def reset_test_data():
#     connection = create_connection()
#     cursor = connection.cursor()

#     cursor.execute("DELETE FROM users WHERE id = 4")

#     connection.commit()
#     connection.close()

#     print("Test data deleted successfully.")
# def update_admin_password(user_id, new_password):

#     connection = create_connection()
#     cursor = connection.cursor()

#     hashed_password = generate_password_hash(new_password)

#     cursor.execute("""
#         UPDATE users
#         SET password = ?
#         WHERE id = ?
#         AND role = 'admin'
#     """, (hashed_password, user_id))

#     print("Updated rows:", cursor.rowcount, flush=True)

#     connection.commit()
#     connection.close()

#     return cursor.rowcount > 0
# def add_test_data():
#     add_test_experts()
#     add_test_deliveries()


# def add_test_experts():

#     for i in range(1, 31):

#         tc_no = f"800000000{i:02d}"
#         password = "1234"
#         role = "expert"
#         first_name = f"TestExpert{i}"
#         last_name = "Test"

#         result = add_user(
#             tc_no,
#             password,
#             role,
#             first_name,
#             last_name
#         )

#         if result:
#             print(f"Expert {i} added: {first_name} {last_name}")
#         else:
#             print(f"Expert {i} could not be added.")
# def add_test_deliveries():

#     connection = create_connection()
#     cursor = connection.cursor()

#     # Aktif farmer ID'lerini al
#     cursor.execute("""
#         SELECT id
#         FROM farmers
#         WHERE is_active = 1
#         ORDER BY id
#     """)

#     farmers = [row[0] for row in cursor.fetchall()]

#     # Aktif expert ID'lerini al
#     cursor.execute("""
#         SELECT id
#         FROM users
#         WHERE role = 'expert'
#         AND is_active = 1
#         ORDER BY id
#     """)

#     experts = [row[0] for row in cursor.fetchall()]

#     connection.close()

#     if not farmers:
#         print("No active farmers found.")
#         return

#     if not experts:
#         print("No active experts found.")
#         return

#     for i in range(1, 31):

#         farmer_id = farmers[(i - 1) % len(farmers)]
#         expert_id = experts[(i - 1) % len(experts)]

#         delivery_date = f"2026-08-{(i % 28) + 1:02d}"

#         gross_weight = 50 + (i * 5)

#         # Yağmurluysa %10 kesinti
#         is_rainy = 1 if i % 3 == 0 else 0

#         if is_rainy:
#             net_weight = gross_weight * 0.9
#         else:
#             net_weight = gross_weight

#         payment_option = "Immediate" if i % 2 == 0 else "Deferred"

#         add_delivery(
#             farmer_id,
#             expert_id,
#             delivery_date,
#             gross_weight,
#             net_weight,
#             is_rainy,
#             payment_option
#         )

#         print(
#             f"Delivery {i} added | "
#             f"Farmer ID: {farmer_id} | "
#             f"Expert ID: {expert_id} | "
#             f"Date: {delivery_date}"
#         )
