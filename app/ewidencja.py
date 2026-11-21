"""Zgłoszenie zmian danych EGiB według fotografii użytkownika."""
from __future__ import annotations

import datetime
import io
import re
from docx import Document
from app import teryt

POLA = {
    'zglaszajacy': ('Zgłaszający zmianę — imię i nazwisko / nazwa', 400),
    'adres1': ('Adres korespondencyjny — ulica i numer', 300),
    'adres2': ('Kod pocztowy i miejscowość', 200),
    'telefon': ('Numer telefonu', 40), 'email': ('Adres e-mail', 254),
    'miejscowosc': ('Miejscowość sporządzenia', 120), 'data': ('Data zgłoszenia', 10),
    'gmina': ('Nazwa jednostki ewidencyjnej — gmina', 200),
    'obreb': ('Nazwa obrębu ewidencyjnego — miejscowość', 200),
    'opis_zmian': ('Opis zgłaszanych zmian', 3000), 'zalaczniki': ('Załączniki do zgłoszenia', 1500),
}
ROLE = [('wlasciciel', 'Właściciel'), ('wladajacy', 'Władający')]
EMAIL = re.compile(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+")
DZIALKA = re.compile(r'\d+(?:/\d+)?')


def domyslne(dane, dzisiaj):
    pierwszy = (dane.get('inwestorzy') or [{}])[0]
    ulica = ' '.join(x for x in [pierwszy.get('ulica', ''), pierwszy.get('nr_domu', '')] if x)
    if not pierwszy.get('ulica') and pierwszy.get('nr_domu'):
        ulica = f"{pierwszy.get('miejscowosc', '')} {pierwszy['nr_domu']}".strip()
    if pierwszy.get('nr_lokalu'):
        ulica += '/' + pierwszy['nr_lokalu']
    return {'zglaszajacy': ', '.join(i.get('imie_nazwisko', '') for i in dane.get('inwestorzy', [])),
            'adres1': ulica, 'adres2': ' '.join(x for x in [pierwszy.get('kod_pocztowy', ''), pierwszy.get('miejscowosc', '')] if x),
            'miejscowosc': dane.get('adres_inwestycji', {}).get('miejscowosc', ''), 'data': dzisiaj,
            'gmina': dane.get('nieruchomosc', {}).get('gmina', ''),
            'obreb': dane.get('adres_inwestycji', {}).get('miejscowosc', ''),
            'telefon': dane.get('zakonczenie', {}).get('telefon_inwestora', '')}


def _norm_gminy(tekst):
    tekst = re.sub(r'^(?:gmina|miasto)\s+', '', tekst.strip(), flags=re.I)
    return re.sub(r'[\s-]', '', tekst).casefold()


def odczytaj_z_formularza(formularz, dane):
    wynik = {}
    for nazwa, (etykieta, limit) in POLA.items():
        if len(formularz.getlist('egib-' + nazwa)) > 1:
            raise ValueError('EGiB: pole nie może być przesłane więcej niż raz.')
        wartosc = formularz.get('egib-' + nazwa, '').strip()
        if len(wartosc) > limit or any(ord(c) < 32 and c not in '\r\n\t' for c in wartosc):
            raise ValueError(f'EGiB: pole „{etykieta}” jest za długie lub zawiera niedozwolony znak.')
        wynik[nazwa] = wartosc
    for nazwa in ['rola', 'zgoda_email']:
        if len(formularz.getlist('egib-' + nazwa)) > 1:
            raise ValueError('EGiB: wybór nie może być przesłany więcej niż raz.')
    wynik['rola'] = formularz.get('egib-rola', '')
    if wynik['rola'] not in {kod for kod, _ in ROLE}:
        raise ValueError('EGiB: wybierz, czy zgłaszasz zmianę jako właściciel czy władający.')
    zgoda = formularz.get('egib-zgoda_email', '')
    if zgoda not in {'', 'tak'}:
        raise ValueError('EGiB: niepoprawny wybór zgody na korespondencję elektroniczną.')
    wynik['zgoda_email'] = zgoda == 'tak'
    for nazwa in ['zglaszajacy', 'adres1', 'adres2', 'miejscowosc', 'data', 'gmina', 'obreb', 'opis_zmian']:
        if not wynik[nazwa]:
            raise ValueError(f'EGiB: uzupełnij „{POLA[nazwa][0]}”.')
    try:
        data = datetime.datetime.strptime(wynik['data'], '%d.%m.%Y').date()
        if data.strftime('%d.%m.%Y') != wynik['data']:
            raise ValueError()
    except ValueError:
        raise ValueError('EGiB: podaj prawidłową datę w formacie DD.MM.RRRR.')
    if wynik['email'] and not EMAIL.fullmatch(wynik['email']):
        raise ValueError('EGiB: podaj poprawny adres e-mail.')
    if wynik['zgoda_email'] and not wynik['email']:
        raise ValueError('EGiB: zgoda na korespondencję elektroniczną wymaga podania adresu e-mail.')
    if wynik['telefon'] and (not re.fullmatch(r'[+\d\s()\-]+', wynik['telefon']) or not 7 <= len(re.sub(r'\D', '', wynik['telefon'])) <= 15):
        raise ValueError('EGiB: sprawdź numer telefonu — dozwolone są cyfry, spacje, nawiasy, + i myślnik.')
    dzialki = dane['adres_inwestycji'].get('nr_dzialki', '').strip()
    if not dzialki or len(dzialki) > 500:
        raise ValueError('EGiB: uzupełnij numery działek w sekcji nieruchomości.')
    lista = re.split(r'[,;]\s*', dzialki)
    if any(not DZIALKA.fullmatch(n.strip()) for n in lista) or len(set(n.strip() for n in lista)) != len(lista):
        raise ValueError('EGiB: numery działek podaj bez powtórzeń, np. 123/4, 125, 126/2.')
    jednostka = teryt.z_identyfikatora(dane['adres_inwestycji'].get('identyfikator_dzialki', ''))
    if jednostka and jednostka.gmina and _norm_gminy(wynik['gmina']) != _norm_gminy(jednostka.gmina):
        raise ValueError('EGiB: gmina nie zgadza się z identyfikatorem działki. Sprawdź źródło i popraw dane.')
    return wynik


def kontekst(dane):
    e = dane.get('egib', {})
    def wpis(nazwa, dlugosc=70):
        return e.get(nazwa, '').strip() or '.' * dlugosc
    def linie(nazwa, ile):
        return e.get(nazwa, '').strip() or '\n'.join(['.' * 165] * ile)
    miejsce_data = ' '.join(x for x in [e.get('miejscowosc', ''), e.get('data', '')] if x)
    return {nazwa: wpis(nazwa) for nazwa in ['zglaszajacy', 'adres1', 'adres2', 'telefon', 'email']} | {
        'data': wpis('data', 45),
        'miejsce_data': miejsce_data or '.' * 65, 'gmina': wpis('gmina', 80), 'obreb': wpis('obreb', 80),
        'dzialki': dane.get('adres_inwestycji', {}).get('nr_dzialki', '').strip() or '.' * 100 + '\n' + '.' * 150,
        'opis_zmian': linie('opis_zmian', 7), 'zalaczniki': linie('zalaczniki', 3)}


def zastosuj_warianty(zawartosc, wybrane):
    d = Document(io.BytesIO(zawartosc))
    for p in d.paragraphs:
        for run in p.runs:
            if run.style.name in {'EGiB_wlasciciel', 'EGiB_wladajacy'} and wybrane.get('rola'):
                run.underline = run.style.name == 'EGiB_' + wybrane['rola']
            if run.style.name == 'EGiB_zgoda':
                run.text = '☒' if wybrane.get('zgoda_email') else '☐'
    out = io.BytesIO(); d.save(out)
    return out.getvalue()
