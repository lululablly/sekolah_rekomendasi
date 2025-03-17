from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# Path ke file CSV
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'univ_indonesia.csv')

# Fungsi untuk membaca dataset
def baca_dataset_sekolah():
    try:
        df = pd.read_csv(CSV_PATH)  # Baca file CSV
        return df
    except FileNotFoundError:
        print(f"File tidak ditemukan: {CSV_PATH}")
        return pd.DataFrame()  # Kembalikan DataFrame kosong jika file tidak ditemukan

# Definisikan class Sekolah
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

        skor_akreditasi = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}.get(self.akreditasi, 0)
        skor_biaya = 5 - self.biaya
        skor_fasilitas = self.fasilitas
        skor_lokasi = {'Pusat Kota': 5, 'Kecamatan': 4, 'Pedesaan': 3}.get(self.lokasi, 0)
        skor_jarak = 5 - self.jarak

        total_skor = (skor_akreditasi * bobot_akreditasi +
                      skor_biaya * bobot_biaya +
                      skor_fasilitas * bobot_fasilitas +
                      skor_lokasi * bobot_lokasi +
                      skor_jarak * bobot_jarak)

        # Bulatkan skor menjadi 2 angka di belakang koma
        return round(total_skor, 2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cari-sekolah', methods=['GET'])
def cari_sekolah():
    kata_kunci = request.args.get('q', '').lower()  # Ambil kata kunci pencarian
    df = baca_dataset_sekolah()

    # Filter data berdasarkan kata kunci
    if not df.empty:
        hasil_pencarian = df[df['Nama'].str.lower().str.contains(kata_kunci)]  # Gunakan kolom 'Nama'
        hasil_pencarian = hasil_pencarian.to_dict('records')  # Konversi ke format dictionary
    else:
        hasil_pencarian = []

    # Format hasil untuk Select2
    hasil_format = [{'id': row['No'], 'text': row['Nama']} for row in hasil_pencarian]  # Gunakan kolom 'No' dan 'Nama'
    return jsonify(hasil_format)

@app.route('/rekomendasi', methods=['POST'])
def rekomendasi():
    nama = request.form['nama']
    lokasi = request.form['lokasi']
    akreditasi = request.form['akreditasi']
    biaya = int(request.form['biaya'])
    fasilitas = int(request.form['fasilitas'])
    jarak = int(request.form['jarak'])

    sekolah = Sekolah(nama, lokasi, akreditasi, biaya, fasilitas, jarak)
    skor = sekolah.hitung_skor()

    return render_template('result.html', nama=sekolah.nama, skor=skor)

if __name__ == '__main__':
    app.run(debug=True)
