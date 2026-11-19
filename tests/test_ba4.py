"""BA-4: warianty druku ze zdjęcia, dane źródeł, format i blokady błędnych wniosków."""
import io
import re
import zipfile
from pathlib import Path

import pytest
from docx import Document
from werkzeug.datastructures import MultiDict
from app.main import app, _dane_z_formularza
from app.generator import generuj_dokumenty

BASE = {
    'dokumenty': 'ba4', 'wybor_potwierdzony': 'tak', 'nazwa_inwestycji': 'Budowa domu jednorodzinnego',
    'inw-0-imie_nazwisko': 'Magdalena Lis', 'inw-0-miejscowosc': 'Nowy Targ',
    'inw-0-ulica': 'ul. Przykładowa', 'inw-0-nr_domu': '12', 'inw-0-kod_pocztowy': '34-400',
    'adres-miejscowosc': 'Nowy Targ', 'adres-nr_dzialki': '1401/2', 'adres-ulica': 'ul. Testowa',
    'adres-nr_domu': '25', 'ba4-data_wniosku': '19.11.2026', 'ba4-rodzaj': 'budowa',
    'ba4-cel': 'rozpoczecie', 'ba4-podstawa': 'pozwolenie_budowa', 'ba4-kolejnosc': 'pierwszy',
    'ba4-deklaracja1': 'potwierdzam', 'ba4-deklaracja2': 'nie_dotyczy',
    'ba4-organ': 'Starostę Nowotarskiego', 'ba4-znak': 'TEST.BA4.2025.501', 'ba4-data_pozwolenia': '11.03.2025',
}


def dokument(formularz):
    with app.test_client() as client:
        response = client.post('/generuj', data=formularz)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        names = z.namelist()
        assert names == ['BA-4_Wniosek_o_dziennik_Lis.docx']
        return Document(io.BytesIO(z.read(names[0])))


def test_pierwszy_dziennik_i_stala_tresc_drukowana():
    d = dokument(BASE)
    text = '\n'.join(p.text for p in d.paragraphs) + '\n'.join(c.text for t in d.tables for row in t.rows for c in row.cells)
    for part in ['BA-4', 'Magdalena Lis', 'Starostę Nowotarskiego', '1401/2', '11.03.2025',
                 'art. 233 Kodeksu karnego', 'Ostateczna decyzja o pozwoleniu', '* niepotrzebne skreślić']:
        assert part in text
    assert '{{' not in text
    punkt2 = next(p for p in d.paragraphs if p.text.startswith('* 2)'))
    punkt3 = next(p for p in d.paragraphs if p.text.startswith('* 3)'))
    assert all(r.font.strike for r in punkt2.runs if r.text)
    assert all(r.font.strike for r in punkt3.runs if r.text)
    budowa = next(r for p in d.paragraphs for r in p.runs if r.style.name == 'BA4_rodzaj_budowa')
    rozbiorka = next(r for p in d.paragraphs for r in p.runs if r.style.name == 'BA4_rodzaj_rozbiorka')
    assert not budowa.font.strike and rozbiorka.font.strike


def test_kolejny_zagubiony_dziennik_i_formatowanie():
    form = BASE | {'ba4-kolejnosc': 'kolejny', 'ba4-poprzedni_numer': 'DB/17/2025',
                   'ba4-posiadanie': 'posiadalem', 'ba4-stan': 'zagubiony',
                   'ba4-okolicznosci': 'Zagubiono podczas przeprowadzki & porządkowania dokumentacji.',
                   'format-kolor': 'granatowy', 'format-pogrubienie': 'tak', 'format-rozmiar': 'wiekszy'}
    d = dokument(form)
    runs = [r for p in d.paragraphs for r in p.runs]
    run = next(r for r in runs if r.text == 'DB/17/2025')
    assert run.bold and str(run.font.color.rgb) == '1F3864' and run.font.size.pt == 13
    stale = next(r for r in runs if 'Jednocześnie - świadomy' in r.text)
    assert str(stale.font.color.rgb) != '1F3864'
    assert any('Zagubiono podczas przeprowadzki & porządkowania' in r.text for r in runs)
    assert not next(r for r in runs if r.style.name == 'BA4_stan_zagubiony').font.strike
    assert next(r for r in runs if r.style.name == 'BA4_stan_zapisany').font.strike


def test_rozbiorka_i_zgloszenie_skresla_caly_prefiks_pozwolenia():
    form = BASE | {'ba4-rodzaj': 'rozbiorka', 'ba4-podstawa': 'zgloszenie'}
    d = dokument(form)
    runs = [r for p in d.paragraphs for r in p.runs]
    assert next(r for r in runs if r.style.name == 'BA4_prefiks_pozwolenie').font.strike
    assert not next(r for r in runs if r.style.name == 'BA4_podstawa_zgloszenie').font.strike
    assert next(r for r in runs if r.style.name == 'BA4_rzeczownik_budowa').text == 'rozbiórki '


@pytest.mark.parametrize('zmiany,blad', [
    ({'ba4-kolejnosc': 'kolejny'}, 'poprzedni numer'),
    ({'ba4-data_pozwolenia': '31.02.2025'}, 'poprawną datą'),
    ({'ba4-data_pozwolenia': '20.11.2026'}, 'późniejsza'),
    ({'ba4-rodzaj': 'rozbiorka'}, 'nie pasuje'),
    ({'ba4-rodzaj': 'inne'}, 'niedozwolony'),
    ({'ba4-deklaracja1': ''}, 'wybierz'),
    ({'ba4-organ': ''}, 'uzupełnij'),
    ({'ba4-znak': 'X' * 121}, 'za długie'),
    ({'adres-nr_dzialki': ''}, 'numer działki'),
    ({'inw-0-nr_domu': ''}, 'adresie każdego inwestora'),
    ({'ba4-kolejnosc': 'kolejny', 'ba4-poprzedni_numer': 'DB/7', 'ba4-posiadanie': 'posiadalem', 'ba4-stan': 'zagubiony'}, 'opisz okoliczności'),
])
def test_bledny_wniosek_nie_przechodzi(zmiany, blad):
    with app.test_client() as client:
        response = client.post('/generuj', data=BASE | zmiany)
    assert response.status_code == 400
    assert blad in response.get_data(as_text=True)


def test_podwojna_opcja_odrzucona():
    form = MultiDict(BASE)
    form.add('ba4-rodzaj', 'rozbiorka')
    with app.test_client() as client:
        assert client.post('/generuj', data=form).status_code == 400


def test_wybor_ba4_pokazuje_pola_bez_zaznaczania_oswiadczen():
    fixture = Path(__file__).parent / 'fixtures' / 'obiegowka_testowa_pelna.docx'
    with app.test_client() as client, fixture.open('rb') as f:
        response = client.post('/wybierz-dokumenty', data={'obiegowka': (f, 'obiegowka.docx')})
        assert 'BA-4 — wniosek o wydanie dziennika' in response.get_data(as_text=True)
        token = re.search(r'name="token" value="([^"]+)"', response.get_data(as_text=True)).group(1)
        response = client.post('/podglad', data={'token': token, 'dokumenty': 'ba4'})
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'id="ba4-kolejny" hidden' in html
    assert 'name="ba4-deklaracja1"' in html and 'name="ba4-deklaracja2"' in html
    assert '<option value="potwierdzam" selected' not in html
    assert 'name="zak-ep"' not in html and 'name="data_pelnomocnictwa"' not in html


def test_pierwszy_dziennik_ignoruje_stare_dane_poprzedniego():
    f = MultiDict(BASE | {'ba4-poprzedni_numer': 'STARY', 'ba4-posiadanie': 'posiadam', 'ba4-stan': 'zapisany'})
    assert _dane_z_formularza(f)['ba4']['poprzedni_numer'] == ''


def test_inne_dokumenty_nie_wymagaja_ba4():
    f = MultiDict({'dokumenty': 'pelnomocnictwo', 'inw-0-imie_nazwisko': 'Jan Testowy', 'ba4-rodzaj': 'niepoprawny'})
    assert 'ba4' not in _dane_z_formularza(f)


def test_decyzja_rozbiorki_dostarcza_dane_do_ba4():
    from app.scalanie_zrodel import odczytaj_zestaw
    d = Document()
    for line in ['STAROSTA NOWOTARSKI', 'Nasz znak: TEST.ROZBIORKA.42', 'DECYZJA NR 42/2025',
                 'Nowy Targ, dnia 08.09.2025 r.', 'UDZIELAM POZWOLENIA NA ROZBIÓRKĘ',
                 'Rozbiórka budynku gospodarczego',
                 'na działce ewid. nr 1603/5, położonej w miejscowości Nowy Targ, obręb 0001, jednostka ewidencyjna 121101_1,',
                 'UZASADNIENIE', 'Inwestorzy, tj. Państwo Emilia i Michał Próbka, wystąpili z wnioskiem.']:
        d.add_paragraph(line)
    b = io.BytesIO(); d.save(b)
    dane = odczytaj_zestaw([('decyzja', 'rozbiorka.docx', b.getvalue())])
    assert dane['nazwa_inwestycji'] == 'Rozbiórka budynku gospodarczego'
    assert dane['zakonczenie']['pozwolenie_znak'] == 'TEST.ROZBIORKA.42'
    assert dane['zakonczenie']['pozwolenie_data'] == '08.09.2025'
    assert len(dane['inwestorzy']) == 2 and not dane['blokada_zestawu']
