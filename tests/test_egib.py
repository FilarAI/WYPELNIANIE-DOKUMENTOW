"""Odtworzone zgłoszenie EGiB: dane, rola, dobrowolna zgoda i blokady błędów."""
import io
import re
import zipfile
from pathlib import Path

import pytest
from docx import Document
from werkzeug.datastructures import MultiDict
from app.main import app, _dane_z_formularza
from app import ewidencja

BASE = {
    'dokumenty': 'egib', 'wybor_potwierdzony': 'tak',
    'inw-0-imie_nazwisko': 'Julia Kontrolna', 'inw-0-miejscowosc': 'Nowy Targ',
    'adres-miejscowosc': 'Nowy Targ', 'adres-nr_dzialki': '1704/8',
    'adres-identyfikator_dzialki': '121101_1.0001.1704/8',
    'egib-zglaszajacy': 'Julia Kontrolna', 'egib-adres1': 'ul. Fikcyjna 16/3', 'egib-adres2': '34-400 Nowy Targ',
    'egib-miejscowosc': 'Nowy Targ', 'egib-data': '19.11.2026', 'egib-gmina': 'Nowy Targ',
    'egib-obreb': 'Nowy Targ', 'egib-rola': 'wlasciciel',
    'egib-opis_zmian': 'Ujawnienie zakończonej budowy budynku mieszkalnego na działce 1704/8.',
    'egib-zalaczniki': 'Dokumentacja geodezyjna powykonawcza',
}


def generuj(form):
    with app.test_client() as client:
        response = client.post('/generuj', data=form)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.namelist() == ['EGiB_Zgloszenie_zmian_Kontrolna.docx']
        return Document(io.BytesIO(z.read(z.namelist()[0])))


def runy(d):
    for p in d.paragraphs:
        yield from p.runs
    for table in d.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield from p.runs


def test_odtworzony_druk_i_niezaznaczona_zgoda():
    d = generuj(BASE)
    runs = list(runy(d)); text = '\n'.join(r.text for r in runs)
    for fragment in ['Julia Kontrolna', '1704/8', 'Wydział Geodezji, Katastru i Kartografii',
                     'Klauzula informacyjna administratora danych osobowych', 'iod@nowotarski.pl',
                     'Wniosek nie podlega opłacie skarbowej', '§ 35 pkt 5', '(*) odpowiednie podkreślić']:
        assert fragment in text
    assert '{{' not in text and '☐' in text and '☒' not in text
    assert next(r for r in runs if r.style.name == 'EGiB_wlasciciel').underline
    assert not next(r for r in runs if r.style.name == 'EGiB_wladajacy').underline


def test_wladajacy_z_jawna_zgoda_i_formatowaniem_tylko_danych():
    form = BASE | {'egib-rola': 'wladajacy', 'egib-zgoda_email': 'tak', 'egib-email': 'test+egib@example.invalid',
                   'egib-opis_zmian': 'Aktualizacja <budynku> & powierzchni; www.nowotarski.pl.',
                   'format-kolor': 'granatowy', 'format-pogrubienie': 'tak', 'format-rozmiar': 'wiekszy'}
    d = generuj(form); runs = list(runy(d))
    assert next(r for r in runs if r.style.name == 'EGiB_zgoda').text == '☒'
    assert next(r for r in runs if r.style.name == 'EGiB_wladajacy').underline
    opis = next(r for r in runs if r.text == form['egib-opis_zmian'])
    assert opis.bold and str(opis.font.color.rgb) == '1F3864'
    assert opis.font.size.pt == 12
    rodo = next(r for r in runs if 'Administratorem Pani/Pana' in r.text)
    assert str(rodo.font.color.rgb) != '1F3864'
    footer = next(r for r in runs if r.text == 'www.nowotarski.pl')
    assert str(footer.font.color.rgb) != '1F3864'
    assert str(next(r for r in runs if r.style.name == 'EGiB_wladajacy').font.color.rgb) != '1F3864'


@pytest.mark.parametrize('zmiany,komunikat', [
    ({'egib-zgoda_email': 'tak'}, 'wymaga podania adresu e-mail'),
    ({'egib-email': 'brak-adresu'}, 'poprawny adres e-mail'),
    ({'egib-zgoda_email': 'true'}, 'niepoprawny wybór zgody'),
    ({'egib-rola': 'pelnomocnik'}, 'właściciel czy władający'),
    ({'egib-telefon': 'numer nieznany'}, 'numer telefonu'),
    ({'egib-data': '31.02.2026'}, 'prawidłową datę'),
    ({'egib-opis_zmian': ''}, 'Opis zgłaszanych zmian'),
    ({'egib-opis_zmian': 'X'*3001}, 'za długie'),
    ({'adres-nr_dzialki': ''}, 'uzupełnij numery działek'),
    ({'adres-nr_dzialki': '1704/8, 1704/8'}, 'bez powtórzeń'),
    ({'adres-nr_dzialki': 'działka A'}, 'numery działek podaj'),
    ({'egib-gmina': 'Zakopane'}, 'gmina nie zgadza się'),
    ({'egib-zglaszajacy': ''}, 'Zgłaszający zmianę'),
])
def test_bledy_nie_przechodza(zmiany, komunikat):
    with app.test_client() as client:
        response = client.post('/generuj', data=BASE | zmiany)
    assert response.status_code == 400
    assert komunikat in response.get_data(as_text=True)


def test_zgoda_nie_pojawia_sie_sama_po_podaniu_maila():
    d = generuj(BASE | {'egib-email': 'test@example.invalid'})
    assert next(r for r in runy(d) if r.style.name == 'EGiB_zgoda').text == '☐'


def test_dwie_dzialki_i_brak_opcjonalnego_telefonu_maila_zalacznikow():
    d = generuj(BASE | {'adres-nr_dzialki': '1704/8, 1705', 'egib-zalaczniki': ''})
    assert any('1704/8, 1705' in r.text for r in runy(d))


def test_powtorzony_wybor_zgody_odrzucony():
    form = MultiDict(BASE); form.add('egib-zgoda_email', 'tak'); form.add('egib-zgoda_email', '')
    with app.test_client() as client:
        assert client.post('/generuj', data=form).status_code == 400


def test_podglad_wypelnia_zrodla_nie_zaznacza_roli_ani_zgody():
    fixture = Path(__file__).parent / 'fixtures' / 'obiegowka_testowa_pelna.docx'
    with app.test_client() as client, fixture.open('rb') as f:
        response = client.post('/wybierz-dokumenty', data={'obiegowka': (f, 'obiegowka.docx')})
        token = re.search(r'name="token" value="([^"]+)"', response.get_data(as_text=True)).group(1)
        response = client.post('/podglad', data={'token': token, 'dokumenty': 'egib'})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'value="Krzysztof Testowy"' in html and 'value="Zakopane"' in html
    assert 'name="adres-identyfikator_dzialki"' in html
    assert 'name="egib-zgoda_email" id="egib-zgoda-email" value="tak" checked' not in html
    assert '<option value="wlasciciel" selected' not in html
    assert 'name="ba4-data_wniosku"' not in html and 'name="zak-ep"' not in html


def test_inne_dokumenty_nie_wymagaja_pola_egib():
    d = _dane_z_formularza(MultiDict({'dokumenty': 'pelnomocnictwo', 'inw-0-imie_nazwisko': 'Jan Testowy', 'egib-rola': 'zly'}))
    assert 'egib' not in d
