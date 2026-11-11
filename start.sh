#!/bin/bash

CYAN="\033[36m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"
BOLD="\033[1m"; RESET="\033[0m"

clear
echo -e "${CYAN}${BOLD}"
echo "════════════════════════════════════════"
echo "           JB STORE - PANEL"
echo "════════════════════════════════════════"
echo -e "${RESET}"
echo -e "  ${GREEN}[1]${RESET} Database Saved (Start Server)"
echo -e "  ${RED}[2]${RESET} Close"
echo ""
read -p "Pilih [1/2]: " opt

case "$opt" in
  1)
    if ! command -v python >/dev/null 2>&1; then
      echo -e "${RED}[!] Python tidak ada. Jalankan: pkg install python${RESET}"
      exit 1
    fi

    if ! command -v cloudflared >/dev/null 2>&1; then
      echo -e "${YELLOW}[*] cloudflared tidak ada, install...${RESET}"
      pkg install -y cloudflared 2>/dev/null || true
      if ! command -v cloudflared >/dev/null 2>&1; then
        echo -e "${YELLOW}[*] Fallback download binary cloudflared...${RESET}"
        ARCH=$(uname -m)
        case "$ARCH" in
          aarch64) CF_ARCH=arm64 ;;
          armv7l|armv8l) CF_ARCH=arm ;;
          x86_64) CF_ARCH=amd64 ;;
          *) echo "Arch $ARCH tidak didukung"; exit 1 ;;
        esac
        curl -L -o "$PREFIX/bin/cloudflared" \
          "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${CF_ARCH}"
        chmod +x "$PREFIX/bin/cloudflared"
      fi
    fi

    echo -e "${GREEN}[*] Menjalankan server di port 8080...${RESET}"
    python server.py &
    SERVER_PID=$!
    sleep 1

    echo -e "${GREEN}[*] Membuka Cloudflare Tunnel...${RESET}"
    rm -f cf.log
    cloudflared tunnel --url http://localhost:8080 --no-autoupdate > cf.log 2>&1 &
    TUNNEL_PID=$!

    URL=""
    for i in $(seq 1 30); do
      URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' cf.log | head -n 1)
      [ -n "$URL" ] && break
      sleep 1
    done

    echo ""
    if [ -n "$URL" ]; then
      echo -e "${BOLD}${GREEN}════════════════════════════════════════${RESET}"
      echo -e "  ${BOLD}${CYAN}URL PUBLIK :${RESET} ${URL}"
      echo -e "  ${BOLD}${CYAN}LOCAL      :${RESET} http://localhost:8080"
      echo -e "${BOLD}${GREEN}════════════════════════════════════════${RESET}"
    else
      echo -e "${RED}[!] Gagal ambil URL tunnel. Cek cf.log${RESET}"
    fi

    trap "kill $SERVER_PID $TUNNEL_PID 2>/dev/null; exit" INT TERM
    wait $SERVER_PID
    ;;
  2)
    echo -e "${RED}Bye 👋${RESET}"
    exit 0
    ;;
  *)
    echo "Pilihan tidak valid"
    ;;
esac