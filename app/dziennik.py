"""Dane i warianty BA-4 odtworzonego ze zdjęcia użytkownika."""
from __future__ import annotations

import datetime
import io
from docx import Document

WYBORY = {
    'rodzaj': [('budowa', 'Budowa'), ('rozbiorka', 'Rozbiórka')],
    'cel': [('rozpoczecie', 'Rozpoczęcie robót'), ('kontynuacja', 'Prowadzenie robót')],
    'podstawa': [('pozwolenie_budowa', 'Pozwolenie na budowę'), ('pozwolenie_rozbiorka', 'Pozwolenie na rozbiórkę'), ('zgloszenie', 'Przyjęte zgłoszenie')],
    'kolejnosc': [('pierwszy', 'Pierwszy dziennik'), ('kolejny', 'Kolejny dziennik')],
    'deklaracja1': [('potwierdzam', 'Potwierdzam treść punktu 1'), ('nie_dotyczy', 'Nie dotyczy — skreśl punkt 1')],
    'deklaracja2': [('potwierdzam', 'Potwierdzam treść punktu 2'), ('nie_dotyczy', 'Nie dotyczy — skreśl punkt 2')],
    'posiadanie': [('posiadam', 'Posiadam poprzedni dziennik'), ('posiadalem', 'Posiadałem / posiadałam poprzedni dziennik')],
    'stan': [('zapisany', 'W całości zapisany'), ('zagubiony', 'Zagubiony'), ('zniszczony', 'Zniszczony'), ('inne', 'Inne okoliczności')],
}
ETYKIETY = {
    'rodzaj': 'Dziennik budowy czy rozbiórki', 'cel': 'Zamiar dotyczący robót',
    'podstawa': 'Podstawa prowadzenia robót', 'kolejnosc': 'Który dziennik',
    'deklaracja1': 'Punkt 1 — obowiązek zawiadomienia', 'deklaracja2': 'Punkt 2 — przerwa w budowie',
    'posiadanie': 'Poprzedni dziennik', 'stan': 'Co stało się z poprzednim dziennikiem',
}
POLA = {'data_wniosku': ('Data wniosku', 10), 'organ': ('Organ wydający decyzję lub przyjmujący zgłoszenie — po słowie przez', 200),
        'znak': ('Znak decyzji lub zgłoszenia', 120), 'data_pozwolenia': ('Data decyzji lub zgłoszenia', 10),
        'poprzedni_numer': ('Numer poprzedniego dziennika', 100), 'okolicznosci': ('Okoliczności zagubienia, zniszczenia lub inne', 1000)}


def domyslne(dane, dzisiaj):
    zak = dane.get('zakonczenie', {})
    return {'data_wniosku': dzisiaj, 'organ': zak.get('pozwolenie_organ', ''),
            'znak': zak.get('pozwolenie_znak', ''), 'data_pozwolenia': zak.get('pozwolenie_data', '')}


def _data(wartosc, nazwa):
    try:
        wynik = datetime.datetime.strptime(wartosc, '%d.%m.%Y').date()
        if wynik.strftime('%d.%m.%Y') != wartosc:
            raise ValueError()
        return wynik
    except ValueError:
        raise ValueError(f'BA-4: {nazwa} musi mieć format DD.MM.RRRR i być poprawną datą.')


def odczytaj_z_formularza(formularz, dane):
    wynik = {}
    for pole, (etykieta, limit) in POLA.items():
        if len(formularz.getlist('ba4-' + pole)) > 1:
            raise ValueError('BA-4: pole nie może być przesłane więcej niż raz.')
        wartosc = formularz.get('ba4-' + pole, '').strip()
        if len(wartosc) > limit:
            raise ValueError(f'BA-4: pole „{etykieta}” jest za długie.')
        wynik[pole] = wartosc
    for pole, opcje in WYBORY.items():
        wybrane = formularz.getlist('ba4-' + pole)
        if len(wybrane) > 1 or (wybrane and wybrane[0] not in {'', *(kod for kod, _ in opcje)}):
            raise ValueError('BA-4: niedozwolony lub powtórzony wybór.')
        wynik[pole] = wybrane[0] if wybrane else ''
    for pole in ['rodzaj', 'cel', 'podstawa', 'kolejnosc', 'deklaracja1', 'deklaracja2']:
        if not wynik[pole]:
            raise ValueError(f'BA-4: wybierz „{ETYKIETY[pole]}”.')
    if wynik['podstawa'].startswith('pozwolenie_') and wynik['podstawa'] != 'pozwolenie_' + wynik['rodzaj']:
        raise ValueError('BA-4: rodzaj dziennika nie pasuje do wybranego pozwolenia.')
    for pole in ['data_wniosku', 'organ', 'znak', 'data_pozwolenia']:
        if not wynik[pole]:
            raise ValueError(f'BA-4: uzupełnij „{POLA[pole][0]}”.')
    wniosek = _data(wynik['data_wniosku'], 'Data wniosku')
    pozwolenie = _data(wynik['data_pozwolenia'], 'Data decyzji lub zgłoszenia')
    if pozwolenie > wniosek:
        raise ValueError('BA-4: data decyzji lub zgłoszenia jest późniejsza niż data wniosku.')
    if not dane['nazwa_inwestycji'] or not dane['adres_inwestycji']['miejscowosc'] or not dane['adres_inwestycji']['nr_dzialki']:
        raise ValueError('BA-4: uzupełnij nazwę inwestycji, miejscowość i numer działki.')
    for osoba in dane['inwestorzy']:
        if not osoba['miejscowosc'] or not osoba['nr_domu']:
            raise ValueError('BA-4: uzupełnij miejscowość i numer domu w adresie każdego inwestora.')
    if wynik['kolejnosc'] == 'kolejny':
        if not wynik['poprzedni_numer'] or not wynik['posiadanie'] or not wynik['stan']:
            raise ValueError('BA-4: dla kolejnego dziennika podaj poprzedni numer, posiadanie i stan dziennika.')
        if wynik['stan'] in {'zagubiony', 'zniszczony', 'inne'} and not wynik['okolicznosci']:
            raise ValueError('BA-4: opisz okoliczności dotyczące poprzedniego dziennika.')
    else:
        for pole in ['poprzedni_numer', 'posiadanie', 'stan', 'okolicznosci']:
            wynik[pole] = ''
    return wynik


def kontekst(dane):
    b = dane.get('ba4', {})
    def wpis(wartosc, dlugosc=55):
        return str(wartosc).strip() if str(wartosc or '').strip() else '.' * dlugosc
    adresy = []
    for i in dane.get('inwestorzy', []):
        ulica = ' '.join(x for x in [i.get('ulica', ''), i.get('nr_domu', '')] if x)
        if not i.get('ulica') and i.get('nr_domu'):
            ulica = f"{i.get('miejscowosc', '')} {i['nr_domu']}".strip()
        if i.get('nr_lokalu'):
            ulica += '/' + i['nr_lokalu']
        miasto = ' '.join(x for x in [i.get('kod_pocztowy', ''), i.get('miejscowosc', '')] if x)
        adres = ', '.join(x for x in [ulica, miasto] if x)
        if adres and adres not in adresy:
            adresy.append(adres)
    a = dane.get('adres_inwestycji', {})
    lokalizacja = ' '.join(x for x in [a.get('miejscowosc', ''), a.get('ulica', ''), a.get('nr_domu', '')] if x)
    if a.get('nr_dzialki'):
        lokalizacja += ', dz. ewid. ' + a['nr_dzialki']
    inwestycja = ' — '.join(x for x in [dane.get('nazwa_inwestycji', ''), lokalizacja] if x)
    return {'inwestorzy': wpis(', '.join(i['imie_nazwisko'] for i in dane.get('inwestorzy', [])), 70),
            'adresy': wpis('; '.join(adresy), 70), 'inwestycja': wpis(inwestycja, 155),
            **{pole: wpis(b.get(pole, ''), 35 if pole == 'data_wniosku' else 150 if pole == 'okolicznosci' else 135 if pole in {'organ', 'znak', 'data_pozwolenia'} else 50) for pole in POLA}}


def zastosuj_warianty(zawartosc, wybrane):
    d = Document(io.BytesIO(zawartosc))
    for p in d.paragraphs:
        for run in p.runs:
            nazwa = run.style.name
            if not nazwa.startswith('BA4_'):
                continue
            grupa, kod = nazwa[4:].split('_', 1)
            if grupa == 'prefiks' and wybrane.get('podstawa'):
                run.font.strike = wybrane['podstawa'] == 'zgloszenie'
                continue
            if grupa == 'rzeczownik':
                if wybrane.get('rodzaj') == 'rozbiorka':
                    run.text = 'rozbiórki '
                continue
            wybor = wybrane.get(grupa)
            if wybor:
                run.font.strike = kod != wybor
        if p.text.startswith('* 1)') and wybrane.get('deklaracja1') == 'nie_dotyczy':
            for run in p.runs: run.font.strike = True
        if p.text.startswith('* 2)') and wybrane.get('deklaracja2') == 'nie_dotyczy':
            for run in p.runs: run.font.strike = True
        if p.text.startswith('* 3)') and wybrane.get('kolejnosc') == 'pierwszy':
            for run in p.runs: run.font.strike = True
    out = io.BytesIO(); d.save(out)
    return out.getvalue()
