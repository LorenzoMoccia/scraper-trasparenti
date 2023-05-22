import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import logging
import re
import time
import aiohttp
import asyncio

# Imposta il logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Richiedi all'utente di inserire l'URL della pagina
url = input("Inserisci l'URL della pagina: ")

response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

# Trova il titolo della pagina
page_title = soup.title.string.strip()

# Crea la cartella principale con il titolo della pagina
main_folder = os.path.join('pdf_files', page_title)
os.makedirs(main_folder, exist_ok=True)

# Trova tutti i div con le classi 'frame-layout-0' e 'frame-layout-3' in tutto il documento
divs = soup.find_all('div', class_=re.compile(r'frame-layout-[03]'))

# Estensioni dei documenti consentite
allowed_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.ppt', '.pptx', '.xls', '.p7m',]

# Parola chiave per identificare i documenti simili
keyword = 'PIAO'

# Dizionario per raggruppare i documenti simili
document_groups = {}

async def download_file(session, url, filepath):
    async with session.get(url) as response:
        if response.status == 200:
            with open(filepath, 'wb') as f:
                f.write(await response.read())
            logging.info(f"Scaricato {filepath}")
            print(f"Download completo: {filepath}")
        else:
            logging.error(f"Errore nel scaricare {filepath}, codice di stato: {response.status}")
            print(f"Errore nel scaricare: {filepath} (Codice di stato: {response.status})")

async def main():
    async with aiohttp.ClientSession() as session:
        for div in divs:
            div_id = div.get('id', '')
            if not div_id.startswith('c'):
                continue

            header = div.find('header')
            if header is None:
                continue
            title = header.text.strip()

            attachment_links = []
            links = div.find_all('a')
            if links is not None:
                attachment_links = [link['href'] for link in links if any(link['href'].lower().endswith(ext) for ext in allowed_extensions)]

            if not attachment_links:
                continue

            title = title.replace('/', '_')

            if keyword in title:
                if keyword not in document_groups:
                    folder_path = os.path.join(main_folder, keyword)
                    document_groups[keyword] = folder_path
                    os.makedirs(folder_path, exist_ok=True)
            else:
                folder_path = os.path.join(main_folder, title)
                os.makedirs(folder_path, exist_ok=True)

            tasks = []
            for attachment_link in attachment_links:
                attachment_link = urljoin(url, attachment_link)
                filename = attachment_link.split('/')[-1]
                filepath = os.path.join(folder_path, filename)
                print(f"Downloading attachment: {attachment_link}")
                tasks.append(download_file(session, attachment_link, filepath))

            await asyncio.gather(*tasks)

            print("\n---")
            print(f"Cartella: {title}")
            print(f"Numero di allegati: {len(attachment_links)}")
            print("Allegati scaricati:")
            for attachment_link in attachment_links:
                filename = attachment_link.split('/')[-1]
                print(f" - {filename}")
            print("---\n")

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
