import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import logging
import re
import time

# Imposta il logging
logging.basicConfig(filename='scraper.log', level=logging.INFO, format='%(asctime)s %(message)s')

# Richiedi all'utente di inserire l'URL della pagina
url = input("Inserisci l'URL della pagina: ")

response = requests.get(url)

soup = BeautifulSoup(response.text, 'html.parser')

# Trova tutti i div con le classi 'frame-layout-0' e 'frame-layout-3' in tutto il documento
divs = soup.find_all('div', class_=re.compile(r'frame-layout-[03]'))

# Crea la cartella pdf_files se non esiste
if not os.path.exists('pdf_files'):
    os.makedirs('pdf_files')

# Estensioni dei documenti consentite
allowed_extensions = ['.pdf', '.doc', '.docx', '.xlsx', '.ppt', '.pptx', '.xls', '.p7m',]

# Parola chiave per identificare i documenti simili
keyword = 'PIAO'

# Dizionario per raggruppare i documenti simili
document_groups = {}

for div in divs:
    # Controlla se l'ID del div inizia con 'c'
    div_id = div.get('id', '')
    if not div_id.startswith('c'):
        continue

    # Trova l'header per il titolo della cartella
    header = div.find('header')
    if header is None:
        continue
    title = header.text.strip()

    # Trova tutti i link nel div
    links = div.find_all('a')
    document_links = []  # Inizializza la variabile prima dell'if
    if links is not None:
        # Estrae tutti i link con estensioni di file consentite
        document_links = [link['href'] for link in links if any(link['href'].lower().endswith(ext) for ext in allowed_extensions)]

    # Se non ci sono documenti, cerca in altri div
    if not document_links:
        previous_div = div.find_previous_sibling('div')
        if previous_div:
            previous_links = previous_div.find_all('a')
            document_links = [link['href'] for link in previous_links if any(link['href'].lower().endswith(ext) for ext in allowed_extensions)]

    # Se non ci sono ancora documenti, salta alla prossima iterazione
    if not document_links:
        continue

    # Sostituisci le barre '/' nel titolo con '_'
    title = title.replace('/', '_')

    # Controlla se il titolo contiene la parola chiave per i documenti simili
    if keyword in title:
        # Verifica se esiste già una cartella per il gruppo di documenti simili
        if keyword in document_groups:
            folder_path = document_groups[keyword]
        else:
            folder_path = os.path.join('pdf_files', keyword)
            document_groups[keyword] = folder_path
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
    else:
        folder_path = os.path.join('pdf_files', title)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    # Scarica i documenti
    for doc_link in document_links:
        # Crea un URL assoluto se necessario
        doc_link = urljoin(url, doc_link)

        # Prepara il nome del file
        filename = doc_link.split('/')[-1]
        filepath = os.path.join(folder_path, filename)

        # Stampa l'URL del documento per il debug
        print(f"Downloading: {doc_link}")

        # Scarica il file
        try:
            response = requests.get(doc_link, allow_redirects=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logging.info(f"Scaricato {filename} in {folder_path}")
                print(f"Download completo: {filename}")
            else:
                logging.error(f"Errore nel scaricare {filename} in {folder_path}, codice di stato: {response.status_code}")
                print(f"Errore nel scaricare: {filename} (Codice di stato: {response.status_code})")
        except Exception as e:
            logging.error(f"Errore nel scaricare {filename} in {folder_path}, errore: {str(e)}")
            print(f"Errore nel scaricare: {filename} ({str(e)})")

        # Pause per evitare di superare i limiti del server
        time.sleep(1)

    print("\n---")
    print(f"Cartella: {title}")
    print(f"Numero di documenti: {len(document_links)}")
    print("Documenti scaricati:")
    for doc_link in document_links:
        filename = doc_link.split('/')[-1]
        print(f" - {filename}")
    print("---\n")
