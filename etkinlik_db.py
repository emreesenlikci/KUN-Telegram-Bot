import requests
from bs4 import BeautifulSoup
import psycopg2
import json
import telegram
from telegram.ext import Updater

# Ayarları çek ve gerekli öğeleri ayarla
with open("settings.json", "r") as f:
    settings = json.load(f)

details = {}

# URL 'e request gönder html parselle ve belirli etiketteki öğeleri seç
url = settings["url_etkinlik"]
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
events_container = soup.find(id="ContentPlaceHolder1_pnl_Duyuru")

# Etkinliğin öğelerini belirle (gorsel, baslik, link, yerleske, tarih, saat)
details['gorsel'] = "https://kapadokya.edu.tr" + events_container.select_one("img")["data-src"]
details['baslik'] = events_container.h3.text
details['link'] = "https://kapadokya.edu.tr" + events_container.a['href']
p_tags = events_container.find_all('p', limit=3)

yerleske, lokasyon, tarih = p_tags
tarih_bol = tarih.text.strip()
date, time = tarih_bol.split(" ")
time = time.replace(".", ":")

details['yerleske'] = yerleske.text.strip()
details['lokasyon'] = lokasyon.text.strip()
details['date'] = date
details['time'] = time

# Etkinlik puanını öğren:
url = details['link']
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')

rating_container = soup.find(id="ContentPlaceHolder1_pnl_Etkinlik_Detail")

if rating_container:
  rating_text = rating_container.text
  if 'Etkinlik Puanı' in rating_text:
    rating = rating_text.split('Etkinlik Puanı')[1].strip()
    rating = rating.replace('\xa0', ' ')
    rating = rating.replace(':', '')
    rating = rating.replace('\n', ' ')
    rating = rating.replace('Paylaş', ' ')
    rating = rating.strip() 
    details['puan'] = rating
  else:
    rating = 'Bilinmiyor'
    details['puan'] = rating
else:
  rating = 'Bilinmiyor'
  details['puan'] = rating


etkinlik_turu = soup.find(id="ContentPlaceHolder1_pnl_Etkinlik_Detail")

if etkinlik_turu:
  etkinlik_turu_text = etkinlik_turu.text
  if 'Etkinlik Türü:' in etkinlik_turu_text:
    etkinlik_tur = etkinlik_turu_text.split('Etkinlik Türü:')[1].strip()
    etkinlik_tur = etkinlik_tur.strip()
    etkinlik_turu_text = etkinlik_tur.split('\r\n')[0]
    etkinlik_turu_text = etkinlik_turu_text.split(' ')[0]
    details['tur'] = etkinlik_turu_text
  else:
    etkinlik_tur = 'Bilinmiyor'
    details['tur'] = etkinlik_tur
else:
  etkinlik_tur = 'Bilinmiyor'
  details['tur'] = etkinlik_tur

# Veri tabanı bağlantısı yap
conn = psycopg2.connect(
    host = settings["host"],
    database = settings["database"],
    port = settings["port"],
    user = settings["user"],
    password = settings["password"]
)

cursor = conn.cursor()

cursor.execute(
        "INSERT INTO etkinlik (gorsel, baslik, link, yerleske, lokasyon, date, time, puan, tur) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (details["gorsel"], details["baslik"], details["link"], details["yerleske"], details["lokasyon"], details["date"], details["time"], details["puan"], details["tur"])
    )
conn.commit()
conn.close()