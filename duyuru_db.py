import requests
from bs4 import BeautifulSoup
import psycopg2
import datetime
import json

# Ayarlardan gerekli bilgileri çekmeyi ayarla
with open("settings.json", "r") as f:
    settings = json.load(f)

# URL 'e request gönder html parselle ve belirli etiketteki öğeleri seç
url = settings["url_duyuru"]
page = requests.get(url)
soup = BeautifulSoup(page.content, "html.parser")
duyurular = soup.select("#ContentPlaceHolder1_pnl_Duyuru")

# Duyurunun öğelerini belirle (baslik, tarih, link)
duyurular_bilgisi = []
for duyuru in duyurular:
    baslik = duyuru.select_one("h3").text
    tarih = duyuru.select_one("p").text
    tarih = tarih.split(", ")[1]
    tarih = datetime.datetime.strptime(tarih, "%d.%m.%Y").strftime("%Y-%m-%d")
    detay_linki = duyuru.select_one("a")["href"]
    detay_linki = "https://kapadokya.edu.tr" + detay_linki
    duyurular_bilgisi.append({
        "baslik": baslik,
        "tarih": tarih,
        "detay_linki": detay_linki
    })

# Duyurunun ayrıntılarını belirle
for duyuru in duyurular_bilgisi:
    detay_url = duyuru["detay_linki"]
    detay_page = requests.get(detay_url)
    detay_soup = BeautifulSoup(detay_page.content, "html.parser")
    detaylar_div = detay_soup.select_one("#ContentPlaceHolder1_pnl_News_Detail")
    detaylar = detaylar_div.select("p")
    ayrintilar = "\n".join([ayrinti.text for ayrinti in detaylar])
    duyuru["ayrintilar"] = ayrintilar

conn = psycopg2.connect(
    host = settings["host"],
    database = settings["database"],
    port = settings["port"],
    user = settings["user"],
    password = settings["password"]
)

cursor = conn.cursor()
for duyuru in duyurular_bilgisi:
    cursor.execute(
        "INSERT INTO duyuru (baslik, tarih, detay_linki, ayrintilar) VALUES (%s, %s, %s, %s)",
        (duyuru["baslik"], duyuru["tarih"], duyuru["detay_linki"], duyuru["ayrintilar"])
    )
conn.commit()
conn.close()