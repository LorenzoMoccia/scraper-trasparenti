import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import re
import time

# Imposta il logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s %(message)s')

url = "https://www.comune.roveredoinpiano.pn.it/index.php?id=31944"

response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

# Trova tutti i div con la classe 'frame-layout-0'
divs = soup.find_all('div', class_='frame-layout-0')

# Crea la cartella pdf_files se non esiste
if not os.path.exists('pdf_files'):
    os.makedirs('pdf_files')

for div in divs:
    # Controlla se l'ID del div inizia con 'c'
    div_id = div.get('id', '')
    if not div_id.startswith('c'):
        continue

    # Trova l'header per il titolo della cartella
    header = div.find('header')
    title = None
    if header is not None:
        title = header.text.strip()

    # Trova l'ul per i documenti
    ul = div.find('ul')
    document_links = []  # Inizializza la variabile prima dell'if
    if ul is not None:
        # Estrae tutti i link di documenti nel 'ul'
        document_links = [li.a['href'] for li in ul.find_all('li') if li.a is not None]

    # Se non ci sono documenti, salta alla prossima iterazione
    if not document_links:
        continue

    # Crea una sottocartella per questa cartella se non esiste
    folder_path = os.path.join('pdf_files', title)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # Scarica i documenti
    for doc_link in document_links:
        # Crea un URL assoluto se necessario
        doc_link = urljoin(url, doc_link)

        # Prepara il nome del file
        filename = doc_link.split('/')[-1]
        filepath = os.path.join(folder_path, filename)  # Modifica qui per utilizzare la sottocartella

        # Controlla se l'URL termina con un'estensione di file
        if not re.search(r'\.\w+$', doc_link):
            print(f"Ignoring: {doc_link}")
            continue

        # Stampa l'URL del documento per il debug
        print(f"Downloading: {doc_link}")

        # Scarica il file
        try:
            response = requests.get(doc_link, allow_redirects=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Scaricato {filename} in {folder_path}")
            else:
                logging.error(f"Errore nel scaricare {filename} in {folder_path}, codice di stato: {response.status_code}")
        except Exception as e:
            logging.error(f"Errore nel scaricare {filename} in {folder_path}, errore: {str(e)}")

        # Pause per evitare di superare i limiti del server
        time.sleep(1)

    print(f"Title: {title}")
    print(f"Document links: {document_links}")
