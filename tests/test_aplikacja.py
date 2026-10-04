import io
import zipfile
from pathlib import Path

import pytest

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def klient():
    app.config["TESTING"] = True
    return app.test_client()


def test_strona_startowa(klient):
    odp = klient.get("/")
    assert odp.status_code == 200
    assert "Wgraj obiegówkę" in odp.get_data(as_text=True)


def test_podglad_pokazuje_dane_i_ostrzezenia(klient):
    with open(FIXTURES / "obiegowka_przyklad.docx", "rb") as f:
        odp = klient.post("/podglad", data={"obiegowka": (f, "obiegowka.docx")}, content_type="multipart/form-data")
    html = odp.get_data(as_text=True)
    assert odp.status_code == 200
    assert 'value="Jan Kowalski"' in html
    assert 'value="120903_4.0002.1358"' in html
    assert 'value="myślenicki"' in html
    assert "różni się między stronami" in html


def test_zly_plik(klient):
    odp = klient.post("/podglad", data={"obiegowka": (io.BytesIO(b"abc"), "plik.pdf")},
                      content_type="multipart/form-data")
    assert "tylko pliki Word .docx" in odp.get_data(as_text=True)


def test_generuj_zip(klient):
    formularz = {
        "nazwa_inwestycji": "BUDOWA DOMU",
        "adres-identyfikator_dzialki": "120903_4.0002.1358", "adres-nr_dzialki": "1358",
        "adres-miejscowosc": "Myślenice", "adres-ulica": "ul. Przykładowa", "adres-nr_domu": "1",
        "inw-0-imie_nazwisko": "Jan Kowalski", "inw-0-plec": "M", "inw-0-miejscowosc": "Myślenice",
        "inw-1712-imie_nazwisko": "Anna Kowalska", "inw-1712-plec": "K", "inw-1712-miejscowosc": "Myślenice",
        "inw-99-imie_nazwisko": "",  # pusty blok inwestora jest pomijany
        "data_pelnomocnictwa": "04.10.2026",
    }
    odp = klient.post("/generuj", data=formularz)
    assert odp.status_code == 200 and odp.mimetype == "application/zip"
    assert "Dokumenty_Kowalski_Kowalska.zip" in odp.headers["Content-Disposition"]
    nazwy = zipfile.ZipFile(io.BytesIO(odp.data)).namelist()
    assert nazwy == ["Pelnomocnictwo_Kowalski_Kowalska.docx", "PB-5_Kowalski_Jan.docx", "PB-5_Kowalska_Anna.docx"]


def test_generuj_bez_inwestora(klient):
    assert klient.post("/generuj", data={"inw-0-imie_nazwisko": ""}).status_code == 400


def test_stopka_pokazuje_wersje_i_folder(klient):
    from app import WERSJA
    from app.main import FOLDER_PROGRAMU

    html = klient.get("/").get_data(as_text=True)
    assert WERSJA in html and FOLDER_PROGRAMU in html


def test_arkusz_stylow_z_wersja(klient):
    # Adres arkusza zmienia się razem z plikiem – przeglądarka nie pokaże starego wyglądu z pamięci.
    assert "styl.css?v=" in klient.get("/").get_data(as_text=True)
