# ParcelHub

**Parcel kampus, lebih mudah.** Sistem pengurusan loker di Pusat Aktiviti Pelajar (PAP), dengan portal penerima, kiosk interaktif dan panel operasi.

![Tests](https://github.com/SweetTooth-mix/Parcel-Hub/actions/workflows/tests.yml/badge.svg)

## Jalankan

Dengan Docker:

```bash
docker compose up --build
```

Buka **http://localhost:8000**. Pilih **Penerima**, **Operator** atau **Admin** pada halaman log masuk untuk mencuba demo. Data disimpan dalam Docker volume `parcelhub-data` dan kekal selepas container dimulakan semula.

Tanpa Docker (Python 3.12):

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
uvicorn app.asgi:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell: gantikan arahan `source` dengan `.venv\Scripts\Activate.ps1`. Node.js hanya diperlukan untuk ujian frontend, bukan untuk menjalankan aplikasi.

## Apa yang boleh dibuat

| Bahagian | Fungsi |
| --- | --- |
| Penerima | Daftar akaun, hantar order melalui web/bot, semak status, terima OTP, QR di web, notifikasi dan sejarah pengambilan |
| Kiosk | OTP/QR, pecahan caj, bayaran demo atau rujukan kaunter, buka pintu, sahkan pengambilan, resit |
| Operator | Terima tugasan pelanggan, pilih saiz/petak, sahkan penyimpanan melalui web/bot, cari parcel dan sahkan bayaran kaunter |
| Admin | Semua fungsi operator, tambah pengguna/peranan, penyelenggaraan, pemulihan insiden, statistik daripada transaksi, eksport CSV |
| Loker | 16 petak S/M/L/XL, model CSS 3D dengan animasi pintu, reservasi atomik, pengesahan pintu melalui simulator atau API peranti |
| Sistem | SQLite persisten, sesi cookie HttpOnly, kawalan peranan, CSRF, had cubaan kod, log audit, peringatan lewat automatik |

Antaramuka menggunakan Bahasa Melayu. Telefon mempunyai navigasi bawah, kad order, butang sentuh besar dan borang satu lajur. Desktop mengekalkan sidebar. Tema dan animasi dikekalkan; tiada font, skrip atau model daripada CDN.

Tema cerah/gelap mengikuti tetapan peranti secara lalai. Gunakan butang bulan/matahari di halaman log masuk atau bar atas untuk menukar tema. Pilihan disimpan dalam pelayar dan kekal selepas refresh atau log keluar. Pilih **Akaun & sistem → Tema paparan → Ikut peranti** untuk kembali mengikuti tema peranti.

Palet navy, teal dan champagne digunakan pada kedua-dua tema. Kad muncul ketika masuk ke paparan, tajuk muncul mengikut perkataan, dan butang memberi respons hover/klik. Skeleton loading digunakan semasa memuatkan rekod; butang menunjukkan pemprosesan sehingga permintaan selesai atau gagal. Carian dan kemas kini latar belakang tidak mengulang animasi masuk. Tetapan **Reduce motion** peranti menghentikan animasi hiasan; kandungan kekal boleh dibaca walaupun API animasi tidak tersedia.

## Aktifkan Telegram (pilihan)

1. Cipta bot khusus ParcelHub melalui [@BotFather](https://t.me/BotFather), menggunakan `/newbot`.
2. Salin `.env.example` ke `.env` jika belum ada. Isi `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_BOT_USERNAME` (tanpa `@`). Token hanya disimpan pada server; jangan commit atau tampal dalam chat.
3. Jalankan aplikasi bersama worker:

   ```bash
   docker compose --profile telegram up --build -d
   ```

4. Log masuk → **Akaun & sistem → Sambung Telegram → Buka Telegram → Start**. Kembali ke portal dan tekan **Saya sudah tekan Start**.
5. Tekan **Hantar mesej ujian** dan semak chat. Untuk berhenti, gunakan **Putuskan sambungan** atau `/stop` dalam bot.

Pelanggan boleh tekan **Order baharu** dalam bot, isi tracking, kurier, saiz dan catatan, kemudian sahkan penghantaran. Pekerja yang menyambungkan akaun sendiri menerima tugasan melalui web dan Telegram. Selepas parcel disimpan, pelanggan menerima **OTP enam digit yang sama** di web dan chat peribadi; QR tersedia di web. E-mel notifikasi masih ditangguhkan; e-mel hanya untuk login.

Worker menggunakan long polling, jadi demo tempatan tidak memerlukan webhook atau domain awam. Server mesti boleh mengakses `api.telegram.org` melalui HTTPS. Jalankan **satu worker sahaja** bagi bot ini. Untuk pautan portal dalam mesej, tetapkan `APP_ORIGIN` kepada URL HTTPS aplikasi anda.

Untuk Python tanpa Docker, tetapkan environment yang sama seperti proses aplikasi (termasuk `DATA_DIR`, `APP_SECRET` dan kedua-dua pemboleh ubah Telegram), kemudian jalankan `python -m app.telegram` dalam terminal kedua. Python tidak memuatkan `.env` secara automatik.

[Butiran penghantaran, retry dan penyelesaian masalah](docs/TELEGRAM.md).

## Cuba aliran order baharu

1. Masuk sebagai **Penerima → Order baharu**. Isi tracking unik, kurier, anggaran saiz dan catatan. Order belum menempah loker atau mengeluarkan kod.
2. Masuk sebagai **Operator → Tugasan → Terima tugasan**. Hanya pekerja yang menerima order boleh menyimpannya.
3. Selepas parcel diterima secara fizikal, pilih **Letak dalam loker**, semak saiz sebenar dan petak.
4. Masukkan parcel dan tutup pintu. Dalam demo, tekan pengesahan simpanan; dalam mod peranti, sensor mesti mengesahkannya.
5. Masuk semula sebagai penerima. Kad order dan notifikasi memaparkan loker, kod serta tarikh luput. Bot menghantar OTP jika akaun telah disambung.
6. Pilih **Kod & QR pengambilan → Gunakan di kiosk**, selesaikan bayaran demo, buka loker dan sahkan parcel diambil. Order berpindah ke Sejarah.

Bot menggunakan aliran yang sama: pelanggan `/order`; pekerja `/tasks`, `/accept ORD-ID`, `/store ORD-ID`, kemudian `/stored ORD-ID` untuk simulasi sahaja. Arahan `/store ORD-ID L` membolehkan saiz sebenar ditukar. Rujuk [panduan order](docs/ORDERS.md).

## Cuba parcel contoh sedia ada

1. Pilih **Penerima** pada halaman log masuk. Akaun demo Aiman mempunyai dua parcel.
2. Pilih **Kod pengambilan**, kemudian **Gunakan di kiosk**.
3. Semak caj dan tekan **Simulasi bayaran**. Tiada wang sebenar dicaj.
4. Tekan **Buka loker**. Pintu pada model 3D akan terbuka.
5. Pilih **Parcel diambil, tutup pintu**. Parcel kini masuk ke sejarah; petak tersedia semula.
6. Log keluar dan masuk sebagai **Operator**. Daftar parcel baharu, pilih penerima/saiz, kemudian sahkan parcel telah disimpan dan pintu ditutup.
7. Masuk semula sebagai **Penerima**. Parcel dan notifikasi baharu telah direkod.

**Telegram dalam demo:** tanpa konfigurasi bot, tiada mesej luaran dihantar. Jika Telegram diaktifkan dan akaun disambung, mesej Telegram adalah sebenar. Gunakan akaun ParcelHub sendiri untuk ujian, bukan akaun demo yang dikongsi.

Kod awal demo: `482910` (A02, biasa) dan `591028` (B01, lewat). Kod ini tidak lagi sah selepas digunakan atau dijana semula. Dapatkan kod terkini daripada portal.

Akaun demo menggunakan domain `.test` dan maklumat rekaan:

| Peranan | E-mel | Kata laluan demo |
| --- | --- | --- |
| Penerima | aiman@demo.parcelhub.test | ParcelDemo2026! |
| Operator | operator@demo.parcelhub.test | ParcelDemo2026! |
| Admin | admin@demo.parcelhub.test | ParcelDemo2026! |

Data demo hanya dijana pada pangkalan data kosong dalam `DEMO_MODE=true`. Akaun demo tidak dicipta dalam mod operasi. Untuk demo baharu tanpa memadam data lama, jalankan Python menggunakan `DATA_DIR=./data-demo-baru`.

## Yang sebenar dan yang disimulasikan

| Keupayaan | Status |
| --- | --- |
| Akaun, peranan, pangkalan data, carian dan sejarah | Berfungsi pada server |
| OTP dan QR | Disahkan pada server; OTP/QR diterbitkan selepas simpanan disahkan, sah 72 jam; melihat kod mengekalkan kod yang sama |
| Pengiraan caj dan rekod transaksi | Berfungsi; wang disimpan sebagai integer sen |
| Notifikasi | Dalam aplikasi; Telegram pilihan selepas pengguna menyambung bot. Peringatan lewat setiap 12 jam |
| Bayaran demo | Simulasi berlabel; tiada sambungan DuitNow atau caj wang sebenar |
| Bayaran operasi | Pengesahan kaunter oleh operator, atau webhook bertandatangan daripada adapter penyedia bayaran |
| Pintu dalam demo | Simulator sensor melalui UI |
| Hardware sebenar | Protokol arahan/acknowledgement tersedia; perlu controller, sensor dan pemetaan relay sebenar |
| Telegram | Integrasi Bot API + giliran penghantaran; perlu token BotFather dan worker untuk menghantar mesej sebenar |
| E-mel / WhatsApp / SMS | Belum disambung |
| Identiti kampus | Pendaftaran tempatan; SSO dan pengesahan e-mel belum disambung |

Sistem ini ialah implementasi aplikasi lengkap untuk demo/pilot satu stesen. Operasi fizikal, bayaran automatik dan penghantaran mesej luaran memerlukan integrasi serta ujian peranti/provider di lokasi. Ia belum disahkan untuk operasi kampus tanpa pengawasan.

## Polisi caj

- S dan M: **RM0.50**; L dan XL: **RM1.00**.
- Caj tambahan **RM1.00 bagi setiap blok enam jam yang bermula**, selepas 24 jam penyimpanan.
- 24 jam tepat: tiada caj lewat. 24 jam + 1 saat: RM1.00. 30 jam + 1 saat: RM2.00.
- Kiosk mengunci sebut harga selama **10 minit**. Bayaran yang telah diterima ditolak daripada jumlah perlu dibayar.
- OTP yang tamat boleh dijana semula oleh penerima, termasuk selepas parcel menjadi lewat.
- Harga ini merupakan tetapan pilot, bukan keputusan kajian kos atau jaminan keuntungan.

## Ujian

```bash
python -m pip install -r requirements.lock
python -m pytest -q
npm ci
npm run check
npm run test:ui
```

Untuk `test:ui`, Python lalai ialah `.venv/bin/python`; pada Windows atau apabila menggunakan Python sistem, tetapkan `PYTHON` kepada executable Python yang mempunyai dependencies aplikasi.

Ujian API meliputi order web/bot, tugasan pekerja serentak, draf bot selepas restart, migrasi, penghantaran kod dan pembatalan kod lama, hak akses, CSRF, pengasingan penerima, OTP tamat/diguna semula, QR, caj sempadan waktu, bayaran idempotent, webhook, perebutan petak, sensor, pemulihan insiden, peringatan dan persistensi. Ujian DOM menggunakan API sebenar melalui `TestClient` tanpa port rangkaian untuk aliran penerima/operator/admin.

Ujian DOM **bukan pengesahan rupa visual dalam browser**. Semakan visual pada browser dan peranti fizikal masih perlu dibuat; tiada screenshot dijadikan bukti ujian dalam repo ini.

## Dokumentasi

- [Order pelanggan, tugasan dan kod](docs/ORDERS.md)
- [Seni bina dan aliran data](docs/ARCHITECTURE.md)
- [Integrasi peranti dan bayaran](docs/INTEGRATIONS.md)
- [Pemasangan operasi, backup dan batasan](docs/OPERATIONS.md)
- [Senario penerimaan](docs/ACCEPTANCE.md)
- Dokumentasi API interaktif: `/api/docs` dalam mod demo

## Struktur

```text
app/                 FastAPI, SQLite, pengesahan dan workflow
app/static/          HTML, CSS dan JavaScript; tiada proses build frontend
app/schema.sql       Skema pangkalan data versi 3, migrasi tambahan automatik
scripts/backup.py    Backup SQLite yang konsisten
scripts/device_simulator.py  Klien ujian kontrak peranti
scripts/payment_event.py     Klien webhook untuk staging
tests/              Ujian transaksi API dan integrasi DOM
docs/               Dokumentasi pemasangan dan integrasi
```
