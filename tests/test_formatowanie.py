"""Wygląd danych w czterech dokumentach, z zachowaniem stałej treści wzorów."""
import copy
import io
import zipfile
from pathlib import Path

import pytest
from docx import Document
from werkzeug.datastructures import MultiDict

from app import formatowanie
from app.generator import generuj_dokumenty
from app.main import app
from app.parser_obiegowki import odczytaj_obiegowke

FIXTURES = Path(__file__).parent / 'fixtures'


def akapity(d):
    yield from d.paragraphs
    for table in d.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from cell.paragraphs


def runy(d):
    return [r for p in akapity(d) for r in p.runs if r.text.strip()]


def tekst(d):
    return '\n'.join(p.text for p in akapity(d))


@pytest.fixture
def dane():
    d = odczytaj_obiegowke(FIXTURES / 'obiegowka_testowa_pelna.docx')
    d['dokumenty'] = ('pelnomocnictwo', 'pb5', 'oswiadczenie', 'zawiadomienie')
    d['data_pelnomocnictwa'] = '19.11.2026'
    d['inwestorzy'].append(copy.deepcopy(d['inwestorzy'][0]) | {'imie_nazwisko': 'Anna Testowa', 'plec': 'K'})
    d['adres_inwestycji']['identyfikator_dzialki'] += ', 121701_1.0005.246/8'
    d['zakonczenie'] = {
        'kierownik_imie_nazwisko': 'Bartłomiej Filar', 'kierownik_adres': 'ul. Sądecka 33h/11',
        'pozwolenie_znak': 'TEST.123.2025', 'pozwolenie_data': '12.03.2025',
        'miejscowosc_sporzadzenia': 'Zakopane', 'data_sporzadzenia': '19.11.2026',
        'ep': '58,40', 'zgodnosc': 'zgodnie', 'teren_doprowadzony': 'nie',
        'tereny_przylegle': 'nie_dotyczy', 'pomiary_powierzchni': 'tak', 'obiekt_nadaje_sie': 'tak',
        'kubatura_mieszkalna': '830,40', 'rodzaje_obiektu': ['nowy', 'mieszkalny'],
        'ogrzewanie': 'pompa_ciepla', 'zalaczniki': ['dziennik_budowy'], 'gaz_sieciowy': 'nie',
    }
    return d


@pytest.mark.parametrize('rozmiar,pogrubienie,kolor', [
    ('normalny', True, 'czarny'), ('wiekszy', False, 'czarny'),
    ('normalny', False, 'granatowy'), ('wiekszy', True, 'granatowy'),
])
def test_wyglad_wszystkich_dokumentow_nie_zmienia_tresci(dane, rozmiar, pogrubienie, kolor):
    bazowe = generuj_dokumenty(dane)
    dane['formatowanie'] = {'rozmiar': rozmiar, 'pogrubienie': pogrubienie, 'kolor': kolor}
    wyniki = generuj_dokumenty(dane)
    assert set(wyniki) == set(bazowe)
    for nazwa, zawartosc in wyniki.items():
        d = Document(io.BytesIO(zawartosc))
        stary = Document(io.BytesIO(bazowe[nazwa]))
        assert tekst(d) == tekst(stary)
        dane_osoby = [r for r in runy(d) if 'Testow' in r.text]
        assert dane_osoby
        for r in dane_osoby:
            assert str(r.font.color.rgb) == ('1F3864' if kolor == 'granatowy' else '000000')
            if pogrubienie:
                assert r.bold
            if rozmiar == 'wiekszy':
                assert r.font.size is not None and r.font.size.pt >= 12.5


def test_tylko_wartosci_sa_wyroznione_nawet_gdy_tekst_sie_powtarza(dane):
    dane['nazwa_inwestycji'] = 'BUDOWA <GARAŻU> & WIATY'
    dane['formatowanie'] = {'rozmiar': 'wiekszy', 'pogrubienie': True, 'kolor': 'granatowy'}
    wyniki = generuj_dokumenty(dane)
    for nazwa, zawartosc in wyniki.items():
        d = Document(io.BytesIO(zawartosc))
        for r in runy(d):
            if (r.text.strip() in {'Ja', 'My', 'Podpis'} or 'DANE INWESTORA' in r.text
                    or 'Imię i nazwisko lub nazwa:' in r.text or 'Województwo:' in r.text
                    or set(r.text.strip()) <= {'.', '…'}):
                assert str(r.font.color.rgb) != '1F3864', (nazwa, r.text)
        if nazwa.startswith('Pelnomocnictwo'):
            wartosc = next(r for r in runy(d) if r.text == dane['nazwa_inwestycji'])
            assert str(wartosc.font.color.rgb) == '1F3864'
            assert wartosc.font.size.pt == 16  # we wzorze 14 pt
            assert 'BUDOWA <GARAŻU> & WIATY' in tekst(d)
        if nazwa.startswith('PB-5'):
            id_dzialki = next(r for r in runy(d) if r.text == '121701_1.0005.246/8')
            assert str(id_dzialki.font.color.rgb) == '1F3864'  # również w załączniku
        if nazwa.startswith('Oswiadczenie'):
            ep = next(r for r in runy(d) if r.text.strip() == '58,40')
            assert str(ep.font.color.rgb) == '1F3864'
            assert 'teren budowy nie został' in tekst(d)
        if nazwa.startswith('Zawiadomienie'):
            wybor = next(r for r in runy(d) if r.text == 'pompa ciepła')
            assert str(wybor.font.color.rgb) == '1F3864' and wybor.underline


def test_zastepowanie_fragmentu_przez_kilka_runow():
    d = Document()
    p = d.add_paragraph()
    p.add_run('Etykieta ...').italic = True
    p.add_run('... koniec').bold = True
    formatowanie.zastap(p, 9, 15, 'Anna & Jan', {'rozmiar': 'normalny', 'pogrubienie': True, 'kolor': 'granatowy'})
    assert p.text == 'Etykieta Anna & Jan koniec'
    assert p.runs[0].text == 'Etykieta ' and str(p.runs[0].font.color.rgb) != '1F3864'
    r = next(r for r in p.runs if r.text == 'Anna & Jan')
    assert r.bold and r.italic and str(r.font.color.rgb) == '1F3864'
    assert p.runs[-1].text == ' koniec' and p.runs[-1].bold


@pytest.mark.parametrize('nazwa,wartosc', [
    ('format-rozmiar', '1000'), ('format-kolor', 'FF0000'),
    ('format-kolor', '<script>alert(1)</script>'), ('format-pogrubienie', 'true'),
])
def test_serwer_odrzuca_niedozwolone_formatowanie(nazwa, wartosc):
    with app.test_client() as klient:
        odp = klient.post('/generuj', data={'inw-0-imie_nazwisko': 'Jan Testowy', nazwa: wartosc})
    assert odp.status_code == 400
    assert 'Niepoprawne ustawienia wyglądu' in odp.get_data(as_text=True)


def test_serwer_odrzuca_podwojny_wybor():
    with app.test_client() as klient:
        odp = klient.post('/generuj', data=MultiDict([
            ('inw-0-imie_nazwisko', 'Jan Testowy'), ('format-kolor', 'czarny'), ('format-kolor', 'granatowy')]))
    assert odp.status_code == 400


def test_formularz_przekazuje_format_do_pobieranego_worda():
    with app.test_client() as klient:
        with (FIXTURES / 'obiegowka_testowa_pelna.docx').open('rb') as plik:
            podglad = klient.post('/podglad', data={'obiegowka': (plik, 'obiegowka.docx')})
        assert 'Wygląd uzupełnionych danych' in podglad.get_data(as_text=True)
        odp = klient.post('/generuj', data={
            'inw-0-imie_nazwisko': 'Jan Testowy', 'dokumenty': 'pelnomocnictwo',
            'format-rozmiar': 'wiekszy', 'format-pogrubienie': 'tak', 'format-kolor': 'granatowy'})
    assert odp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(odp.data)) as z:
        d = Document(io.BytesIO(z.read(z.namelist()[0])))
    r = next(r for r in runy(d) if r.text == 'Jan Testowy')
    assert r.bold and r.font.size.pt == 14 and str(r.font.color.rgb) == '1F3864'
