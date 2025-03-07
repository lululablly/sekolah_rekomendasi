from flask import Flask, render_template, request

app = Flask(__name__)

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

        return total_skor

@app.route('/')
def index():
    return render_template('index.html')

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