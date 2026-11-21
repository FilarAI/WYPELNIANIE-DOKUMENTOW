"""Odczyt pojedynczego źródła i ostrożna podpowiedź jego rodzaju."""
import re
import unicodedata
from app.odczyt_plikow import odczytaj_tekst


def _normalizuj(tekst):
    return unicodedata.normalize('NFKD', tekst.lower().replace('ł', 'l')).encode('ascii', 'ignore').decode()


def sprawdz(zawartosc, nazwa):
    linie, ocr = odczytaj_tekst(zawartosc, nazwa)
    tekst = ' '.join(t for _, t in linie)
    if not tekst.strip():
        raise ValueError('Nie znaleziono czytelnej treści. Wybierz dokument z tekstem lub wyraźniejszy skan.')
    start = _normalizuj(tekst[:5000])
    typ = ''
    # Nagłówek decyzji ma pierwszeństwo przed nazwami stron projektu.
    if re.search(r'\bdecyzja\b', start[:1200]) and re.search(r'zatwierdz|pozwolen|pozwalam', start):
        typ = 'decyzja'
    elif 'obieg' in start or ('inwestor' in start and ('adres inwestycji' in start or 'nazwa inwestycji' in start)):
        typ = 'obiegowka'
    elif re.search(r'projekt budowlany|dokumentacj|projekt zagospodarowania|protokol|oswiadczenie kierownika', start):
        typ = 'teczka'
    return {'typ': typ, 'ocr': ocr, 'stan': 'odczytany'}
