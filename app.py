from flask import Flask, render_template, request, jsonify
import mysql.connector
import pandas as pd
import os

app = Flask(__name__)

# Configure MySQL connection
# Untuk produksi, gunakan variabel lingkungan:
# MYSQL_CONFIG = {
#     'host': os.getenv('MYSQL_HOST', 'localhost'),
#     'user': os.getenv('MYSQL_USER', 'root'),
#     'password': os.getenv('MYSQL_PASSWORD', 'mypassword'),
#     'database': os.getenv('MYSQL_DB', 'universitas_db')
# }
MYSQL_CONFIG = {
    'host': 'lulablly.mysql.pythonanywhere-services.com',
    'user': 'lulablly',
    'password': '',  # Ganti dengan kata sandi MySQL kamu
    'database': 'lulablly$universitas_db'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error koneksi ke MySQL: {err}")
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        # Create universities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                univ_name VARCHAR(255) NOT NULL,
                lokasi VARCHAR(50),
                akreditasi CHAR(1),
                biaya INT,
                fasilitas INT,
                jarak INT
            )
        ''')
        # Create search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                univ_name VARCHAR(255),
                lokasi VARCHAR(50),
                akreditasi CHAR(1),
                biaya INT,
                fasilitas INT,
                jarak INT,
                skor FLOAT,
                search_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add index for faster search
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_univ_name ON universities(univ_name)
        ''')
        conn.commit()
        print("Database berhasil diinisialisasi.")
    except mysql.connector.Error as err:
        print(f"Error saat membuat tabel: {err}")
    finally:
        cursor.close()
        conn.close()

def populate_universities():
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM universities')
        count = cursor.fetchone()[0]
        if count == 0:
            csv_path = os.path.join(os.path.dirname(__file__), 'data', 'univ_indonesia.csv')
            try:
                df = pd.read_csv(csv_path)
                if 'univ_name' not in df.columns:
                    raise KeyError("Kolom 'univ_name' tidak ditemukan di CSV")
                for _, row in df.iterrows():
                    cursor.execute('''
                        INSERT INTO universities (univ_name, lokasi, akreditasi, biaya, fasilitas, jarak)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        row['univ_name'],
                        'Pusat Kota',
                        'A',
                        3,
                        3,
                        3
                    ))
                conn.commit()
                print("Data universitas berhasil dimuat ke database.")
            except FileNotFoundError:
                print(f"File tidak ditemukan: {csv_path}")
            except KeyError as e:
                print(f"Error: {e}")
            except Exception as e:
                print(f"Terjadi kesalahan saat memuat data: {e}")
    except mysql.connector.Error as err:
        print(f"Error saat memeriksa tabel universities: {err}")
    finally:
        cursor.close()
        conn.close()

def baca_dataset_sekolah():
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql("SELECT * FROM universities", conn)
        return df
    except mysql.connector.Error as err:
        print(f"Error saat membaca data: {err}")
        return pd.DataFrame()
    finally:
        conn.close()

class Sekolah:
    def __init__(self, nama, lokasi, akreditasi, biaya, fasilitas, jarak):
        self.nama = nama
        self.lokasi = lokasi
        self.akreditasi = akreditasi
        self.biaya = biaya
        self.fasilitas = fasilitas
        self.jarak = jarak

    def hitung_skor(self):
        bobot_akreditasi = 0.3
        bobot_biaya = 0.25
        bobot_fasilitas = 0.2
        bobot_lokasi = 0.15
        bobot_jarak = 0.1

        # Hitung skor individu
        skor_akreditasi = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}.get(self.akreditasi, 0)
        skor_biaya = 5 - self.biaya
        skor_fasilitas = self.fasilitas
        skor_lokasi = {'Pusat Kota': 5, 'Kecamatan': 4, 'Pedesaan': 3}.get(self.lokasi, 0)
        skor_jarak = 5 - self.jarak

        # Hitung total skor
        total_skor = (skor_akreditasi * bobot_akreditasi +
                      skor_biaya * bobot_biaya +
                      skor_fasilitas * bobot_fasilitas +
                      skor_lokasi * bobot_lokasi +
                      skor_jarak * bobot_jarak)

        # Simpan detail perhitungan
        detail_perhitungan = {
            'akreditasi': {
                'nilai': self.akreditasi,
                'skor': skor_akreditasi,
                'bobot': bobot_akreditasi,
                'kontribusi': round(skor_akreditasi * bobot_akreditasi, 2)
            },
            'biaya': {
                'nilai': self.biaya,
                'skor': skor_biaya,
                'bobot': bobot_biaya,
                'kontribusi': round(skor_biaya * bobot_biaya, 2)
            },
            'fasilitas': {
                'nilai': self.fasilitas,
                'skor': skor_fasilitas,
                'bobot': bobot_fasilitas,
                'kontribusi': round(skor_fasilitas * bobot_fasilitas, 2)
            },
            'lokasi': {
                'nilai': self.lokasi,
                'skor': skor_lokasi,
                'bobot': bobot_lokasi,
                'kontribusi': round(skor_lokasi * bobot_lokasi, 2)
            },
            'jarak': {
                'nilai': self.jarak,
                'skor': skor_jarak,
                'bobot': bobot_jarak,
                'kontribusi': round(skor_jarak * bobot_jarak, 2)
            }
        }

        return round(total_skor, 2), detail_perhitungan

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cari-sekolah', methods=['GET'])
def cari_sekolah():
    query = request.args.get('q', '').lower()
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Gagal terhubung ke database.'}), 500
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, univ_name FROM universities
            WHERE LOWER(univ_name) LIKE %s
        ''', (f'%{query}%',))
        results = cursor.fetchall()

        formatted_results = [{
            'id': row[0],
            'text': row[1]
        } for row in results]
        
        return jsonify(formatted_results)
    except mysql.connector.Error as err:
        print(f"Error saat mencari universitas: {err}")
        return jsonify({'error': f'Error database: {err}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/rekomendasi', methods=['POST'])
def rekomendasi():
    # Get form data
    nama = request.form['nama']
    lokasi = request.form['lokasi']
    akreditasi = request.form['akreditasi']
    try:
        biaya = int(request.form['biaya'])
        fasilitas = int(request.form['fasilitas'])
        jarak = int(request.form['jarak'])
    except ValueError:
        return render_template('index.html', error="Input biaya, fasilitas, dan jarak harus berupa angka.")

    # Validate input
    if biaya < 1 or biaya > 5 or fasilitas < 1 or fasilitas > 5 or jarak < 1 or jarak > 5:
        return render_template('index.html', error="Input biaya, fasilitas, dan jarak harus antara 1 dan 5.")

    if akreditasi not in ['A', 'B', 'C', 'D', 'E']:
        return render_template('index.html', error="Akreditasi harus salah satu dari A, B, C, D, atau E.")

    if lokasi not in ['Pusat Kota', 'Kecamatan', 'Pedesaan']:
        return render_template('index.html', error="Lokasi tidak valid.")

    # Calculate score and get calculation details
    sekolah = Sekolah(nama, lokasi, akreditasi, biaya, fasilitas, jarak)
    skor, detail_perhitungan = sekolah.hitung_skor()

    # Save to search history
    conn = get_db_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO search_history (univ_name, lokasi, akreditasi, biaya, fasilitas, jarak, skor)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (nama, lokasi, akreditasi, biaya, fasilitas, jarak, skor))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error saat menyimpan riwayat: {err}")
        finally:
            cursor.close()
            conn.close()

    # Get recent search history
    conn = get_db_connection()
    history = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT univ_name, lokasi, akreditasi, biaya, fasilitas, jarak, skor
                FROM search_history
                ORDER BY search_time DESC
                LIMIT 5
            ''')
            history = cursor.fetchall()
        except mysql.connector.Error as err:
            print(f"Error saat mengambil riwayat: {err}")
        finally:
            cursor.close()
            conn.close()

    # Prepare result data
    result_data = {
        'nama': nama,
        'skor': skor,
        'detail': {
            'Lokasi': lokasi,
            'Akreditasi': akreditasi,
            'Biaya': biaya,
            'Fasilitas': fasilitas,
            'Jarak': jarak
        },
        'detail_perhitungan': detail_perhitungan
    }

    # Prepare history data
    history_data = [{
        'nama': row[0],
        'lokasi': row[1],
        'akreditasi': row[2],
        'biaya': row[3],
        'fasilitas': row[4],
        'jarak': row[5],
        'skor': row[6]
    } for row in history]

    return render_template('result.html', result=result_data, history=history_data)

if __name__ == '__main__':
    init_db()
    populate_universities()
    app.run(debug=True)
