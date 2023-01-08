print(
    "========== B A Ş L A T I L I Y O R ==========",
    "\nLog:",
    "\nGerekli kütüphaneler kontrol ediliyor...")

import subprocess
import sys
import logging
import os

# Python versiyon kontrol et 3.0< ise güncelle
def python_version():
    try:
        if sys.version_info < (3, 0):
            subprocess.run(['python3', '-m', 'pip', 'install', '--upgrade', 'pip'])
            print('Python güncellendi!')
        else:
            pass
    except Exception as e:
        print("Python güncellerken hata oluştu: ", e)
python_version()

# event_logs.txt oluştur eğer yoksa
file_name = 'event_logs.txt'
file_path = os.path.join(os.getcwd(), file_name)

# logs.txt mevcut ise içeriğini sil
if os.path.exists(file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('')

# Log kayıt türünü ayarla
logging.basicConfig(filename=file_path, filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO, encoding='utf-8', datefmt='%Y-%m-%d %H:%M:%S')

# Kütüphaneleri indirir.
def kutuphaneler():
    try:
        subprocess.run(["pip", "install", "-r", "requirements.txt"])
        print("Kütüphaneler başarıyla indirildi.")
    except Exception as e:
        print("Hata oluştu: ", e)
kutuphaneler()

import json

# Ayarlardan bilgileri çek
with open("settings.json", "r") as f:
    settings = json.load(f)

print("Version:",settings['version'],)

import psycopg2

db_host = settings['host']
db_name = settings['database']
db_port = settings['port']
db_user = settings['user']
db_password = settings['password']

# Veri tabanı bağlantısını kontrol et:
def veritabani_baglanti_kontrol():
    print("Veri Tabanı Bağlantısı Kontrol Ediliyor...")
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )

        cursor = conn.cursor()
        print("Bağlantı Başarılı!")

    except psycopg2.OperationalError as e:
        print("Veri tabanına bağlanırken hata oluştu:\n",e)
    except psycopg2.InterfaceError as e:
        print("Veri tabanına bağlanırken hata oluştu:\n",e)

    cursor.close()
    conn.close()
veritabani_baglanti_kontrol()

# Duyuru ve etkinlik veritabanlarının var olup olmadığını kontrol et
def veritabani_kontrol():
    try:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
            )

        cur = conn.cursor()

        cur.execute("SELECT to_regclass('duyuru')")
        if cur.fetchone()[0] is not None:
            cur.execute("DELETE FROM duyuru")
            print("'duyuru' veritabanı tablosu bulundu (İçeriği silindi!)")
            
        else:
            print("'duyuru' veritabanı tablosu bulunamadı. Oluşturuluyor...")
            cur.execute("CREATE TABLE duyuru (id serial PRIMARY KEY, baslik VARCHAR(512), tarih DATE, detay_linki VARCHAR(512), ayrintilar TEXT)")

        cur.execute("SELECT to_regclass('etkinlik')")
        if cur.fetchone()[0] is not None:
            cur.execute("DELETE FROM etkinlik")
            print("'etkinlik' veritabanı tablosu bulundu (İçeriği silindi!)")
        else:
            print("'etkinlik' veritabanı tablosu bulunamadı. Oluşturuluyor...")
            cur.execute("CREATE TABLE etkinlik (id serial PRIMARY KEY, gorsel VARCHAR(512), baslik VARCHAR(512), link VARCHAR(512), yerleske VARCHAR(512), lokasyon VARCHAR(512), date DATE, time TIME, puan VARCHAR(512), tur VARCHAR(512))")

        conn.commit()
        conn.close()

    except Exception as e:
        print("Veri tabanı sorgularında sorun bulunmakta: ",e)
veritabani_kontrol()

from bs4 import BeautifulSoup
import telegram
import datetime
import requests

# Duyurular adresinden son duyuruyu veri tabanına kaydet:
duyuru_cek = "duyuru_db.py"
exec(open(duyuru_cek).read())
print("Son duyuru çekildi ve veri tabanına kaydedildi.")

# Etkinlikler adresinden son etkinliği veri tabanına kaydet:
etkinlik_cek = "etkinlik_db.py"
exec(open(etkinlik_cek).read())
print("Son etkinlik çekildi ve veri tabanına kaydedildi.")

# Veri tabanından son duyuruyu çek ve telegrama gönder.
def duyuru_telegram_ilk_post():

    bot = telegram.Bot(token=settings["bot_token"])
    conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
    cursor = conn.cursor()
    cursor.execute("SELECT baslik, tarih, detay_linki, ayrintilar FROM duyuru")
    rows = cursor.fetchall()
    duyurular_bilgi = []
    for row in rows:
        duyuru_bilgi = {
            "baslik": row[0],
            "tarih": row[1],
            "detay_linki": row[2],
            "ayrintilar": row[3]
        }
    duyurular_bilgi.append(duyuru_bilgi)
    conn.close()
    for duyuru in duyurular_bilgi:
        button_label = "Bağlantı Adresine Git"
        button = telegram.InlineKeyboardButton(text=button_label, url=f"{duyuru['detay_linki']}")
        keyboard = telegram.InlineKeyboardMarkup([[button]])

        bot.send_message(
            chat_id = settings["chat_id"],
            text=f"❗ **{duyuru['baslik']}**\nTarih: {duyuru['tarih']}\n\nAyrıntılar:\n{duyuru['ayrintilar']}",parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=keyboard
        )
    print("BAŞARILI - Son duyuru telegrama başarıyla paylaşıldı!")
# Veri tabanından son etkinliği çek ve telegrama gönder.
def etkinlik_telegram_ilk_post():
    bot = telegram.Bot(token=settings["bot_token"])
    conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
    cursor = conn.cursor()
    cursor.execute("SELECT gorsel, baslik, link, yerleske, lokasyon, date, time, puan, tur FROM etkinlik")
    rows = cursor.fetchall()

    etkinlikler_bilgi = []
    for row in rows:
        etkinlik_bilgi = {
            "gorsel": row[0],
            "baslik": row[1],
            "link": row[2],
            "yerleske": row[3],
            "lokasyon": row[4],
            "date": row[5],
            "time": row[6],
            "puan": row[7],
            "tur": row[8]
        }
    etkinlikler_bilgi.append(etkinlik_bilgi)
    conn.close()
    for etkinlik in etkinlikler_bilgi:
        button_label = "Bağlantı Adresine Git"
        button = telegram.InlineKeyboardButton(text=button_label, url=f"{etkinlik['link']}")
        keyboard = telegram.InlineKeyboardMarkup([[button]])

        bot.send_photo(
            chat_id = settings["chat_id"],
            photo=requests.get(etkinlik['gorsel']).content,
            caption=f"❗ **{etkinlik['baslik']}**\nBaşlangıç Tarihi: {etkinlik['date']} - {etkinlik['time']}\n\nAyrıntılar:\nYerleşke: {etkinlik['yerleske']}\nLokasyon: {etkinlik['lokasyon']}\nEtkinlik Puanı: {etkinlik['puan']}\nEtkinlik Türü: {etkinlik['tur']}",
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    print("BAŞARILI - Son etkinlik telegrama başarıyla paylaşıldı!")

duyuru_telegram_ilk_post()
etkinlik_telegram_ilk_post()

import time
global duyuru_durum
duyuru_durum = 0
def duyuru_guncel():
    duyuru_guncel_bilgi = []

    # URL 'e request gönder html parselle ve belirli etiketteki öğeleri seç
    url = settings["url_duyuru"]
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    duyurular = soup.select("#ContentPlaceHolder1_pnl_Duyuru")

    for duyuru in duyurular:
        baslik = duyuru.select_one("h3").text
        tarih = duyuru.select_one("p").text
        tarih = tarih.split(", ")[1]
        tarih = datetime.datetime.strptime(tarih, "%d.%m.%Y").strftime("%Y-%m-%d")
        detay_linki = duyuru.select_one("a")["href"]
        detay_linki = "https://kapadokya.edu.tr" + detay_linki
        duyuru_guncel_bilgi.append({
            "baslik": baslik,
            "tarih": tarih,
            "detay_linki": detay_linki
        })

    for duyuru in duyuru_guncel_bilgi:
        detay_url = duyuru["detay_linki"]
        detay_page = requests.get(detay_url)
        detay_soup = BeautifulSoup(detay_page.content, "html.parser")
        detaylar_div = detay_soup.select_one("#ContentPlaceHolder1_pnl_News_Detail")
        detaylar = detaylar_div.select("p")
        ayrintilar = "\n".join([ayrinti.text for ayrinti in detaylar])
        duyuru["ayrintilar"] = ayrintilar

    for duyuru in duyuru_guncel_bilgi:
        ayrinti_text = duyuru['ayrintilar']
        ayrinti = ayrinti_text.replace('\xa0', '')
        duyuru['ayrintilar'] = ayrinti

    conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
    cursor = conn.cursor()
    cursor.execute("SELECT baslik FROM duyuru ORDER BY id DESC LIMIT 1")
    veritabani_en_son_duyuru = cursor.fetchone()
    veritabani_en_son_duyuru = veritabani_en_son_duyuru[0] 
    veritabani_en_son_duyuru = veritabani_en_son_duyuru.strip(",')")

    conn.commit()
    conn.close()

    if veritabani_en_son_duyuru != duyuru['baslik']:
        print("Yeni Duyuru Bulundu! - " + duyuru["baslik"])
        logging.info("Yeni Duyuru Bulundu! - " + duyuru["baslik"])
        for duyuru in duyuru_guncel_bilgi:
            conn = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password
            )
            cursor = conn.cursor()
            cursor.execute(
            "INSERT INTO duyuru (baslik, tarih, detay_linki, ayrintilar) VALUES (%s, %s, %s, %s)",
            (duyuru["baslik"], duyuru["tarih"], duyuru["detay_linki"], duyuru["ayrintilar"])
            )
            conn.commit()
            conn.close()

        bot = telegram.Bot(token=settings["bot_token"])
        for duyuru in duyuru_guncel_bilgi:
            button_label = "Bağlantı Adresine Git"
            button = telegram.InlineKeyboardButton(text=button_label, url=f"{duyuru['detay_linki']}")
            keyboard = telegram.InlineKeyboardMarkup([[button]])

            bot.send_message(
                chat_id = settings["chat_id"],
                text=f"❗ **{duyuru['baslik']}**\nTarih: {duyuru['tarih']}\n\nAyrıntılar:\n{duyuru['ayrintilar']}",parse_mode=telegram.ParseMode.MARKDOWN, reply_markup=keyboard
            )
    else:
        global duyuru_durum
        duyuru_durum = duyuru_durum + 1

etkinlik_durum = 0
def etkinlik_guncel():
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
            rating = rating.replace('\n', ' ')
            rating = rating.replace(':', '')
            rating = rating.replace('Paylaş', ' ')
            rating = rating.strip() 
            details['puan'] = rating
        else:
            rating = 'Bilinmiyor'
            details['puan'] = rating
    else:
        rating = 'Bilinmiyor'
        details['puan'] = rating

    # Etkinlik türünü öğren:
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

    # Veri tabanına bağlan
    conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
    cursor = conn.cursor()
    # Etkinlik tablosundan baslik sütununda en son eklenen veriyi çek:
    cursor.execute("SELECT baslik FROM etkinlik ORDER BY id DESC LIMIT 1")
    veritabani_en_son_etkinlik = cursor.fetchone()[0]
    veritabani_en_son_etkinlik = veritabani_en_son_etkinlik.strip(",')")
    conn.commit()
    conn.close()

    # Veri tabanındaki bilgi ile son çekilen bilgiyi karşılaştır:
    if veritabani_en_son_etkinlik != details['baslik']:
        print("Yeni Etkinlik Bulundu! - " + details["baslik"])
        logging.info("Yeni Etkinlik Bulundu! - " + details["baslik"])
        bot = telegram.Bot(token=settings["bot_token"])
        # Yeni bilgiyi veri tabanına aktar
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )

        cursor = conn.cursor()
        cursor.execute(
        "INSERT INTO etkinlik (gorsel, baslik, link, yerleske, lokasyon, date, time, puan, tur) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (details["gorsel"], details["baslik"], details["link"], details["yerleske"], details["lokasyon"], details["date"], details["time"], details["puan"], details["tur"])
        )
        conn.commit()
        conn.close()

        # Yeni bilgiyi telegramda paylaş
        button_label = "Bağlantı Adresine Git"
        button = telegram.InlineKeyboardButton(text=button_label, url=f"{details['link']}")
        keyboard = telegram.InlineKeyboardMarkup([[button]])

        bot.send_photo(
            chat_id = settings["chat_id"],
            photo=requests.get(details['gorsel']).content,
            caption=f"❗ **{details['baslik']}**\nBaşlangıç Tarihi: {details['date']} - {details['time']}\n\nAyrıntılar:\nYerleşke: {details['yerleske']}\nLokasyon: {details['lokasyon']}\nEtkinlik Puanı: {details['puan']}\nEtkinlik Türü: {details['tur']}",
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=keyboard
            )
    # Eğer bilgiler aynı ise
    else:
        global etkinlik_durum
        etkinlik_durum = etkinlik_durum + 1

print("Duyuru ve Etkinlik takibi başlamıştır. Log kayıtları logs.txt içerisine kaydedilmektedir.")

import threading

# Etkinlikleri yaklaştığı vakite göre Örn: Şimdi başlıyor şeklinde paylaşır.
def etkinlik_takip():
    while True:
        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM etkinlik")

        events = []
        for row in cur:
            event = {
                'gorsel': row[1],
                'baslik': row[2],
                'link': row[3],
                'yerleske': row[4],
                'lokasyon': row[5],
                'date': row[6],
                'time': row[7],
                'puan': row[8],
                'tur': row[9]
            }
            events.append(event)

        now = datetime.datetime.now().time().replace(second=0, microsecond=0)

        for event in events:

            if event['date'] == datetime.date.today() and event['time'] == now:
                print(f"{event['baslik']}, Etkinlik şuan başlıyor")
                logging.info(f"{event['baslik']}, Etkinlik şuan başlıyor")

                bot = telegram.Bot(token=settings["bot_token"])

                button_label = "Bağlantı Adresine Git"
                button = telegram.InlineKeyboardButton(text=button_label, url=f"{event['link']}")
                keyboard = telegram.InlineKeyboardMarkup([[button]])

                bot.send_photo(
                    chat_id = settings["chat_id"],
                    photo=requests.get(event['gorsel']).content,
                    caption=f"❗ETKİNLİK ŞUAN BAŞLIYOR!\n\n**{event['baslik']}**\nBaşlangıç Tarihi: {event['date']} - {event['time']}\n\nAyrıntılar:\nYerleşke: {event['yerleske']}\nLokasyon: {event['lokasyon']}\nEtkinlik Puanı: {event['puan']}\nEtkinlik Türü: {event['tur']}",
                    parse_mode=telegram.ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        time.sleep(60)

print("Etkinlik Zaman Takip başlamıştır. Log kayıtları logs.txt içerisine kaydedilmektedir.")

event_check_thread = threading.Thread(target=etkinlik_takip)
event_check_thread.start()

# Güncel duyuru ve etkinlikleri kontrol eder ve log kaydı geçer.
while True:
    duyuru_guncel()
    etkinlik_guncel()
        # 60 Saniyede bir ayarlı şekilde bilgi iletir.
    log_message = ''
        
    if duyuru_durum == 12:
        duyuru_durum = 0
        log_message += 'Yeni duyuru bulunmamaktadır. '

    if etkinlik_durum == 12:
        etkinlik_durum = 0
        log_message += 'Yeni etkinlik bulunmamaktadır. '

    if log_message:
        logging.info(log_message)
    time.sleep(5)