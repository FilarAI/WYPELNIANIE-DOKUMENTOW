"""Wniosek EGiB o wypis/wyrys: dane, wybory i walidacja."""
import io
import zipfile

import pytest
from docx import Document

from app.main import app

BASE = {
    "dokumenty": "egib_wypis", "wybor_potwierdzony": "tak",
    "inw-0-imie_nazwisko": "Julia Kontrolna", "inw-0-miejscowosc": "Nowy Targ",
    "inw-0-ulica": "ul. Fikcyjna", "inw-0-nr_domu": "16", "inw-0-nr_lokalu": "3",
    "inw-0-kod_pocztowy": "34-400", "inw-0-email": "julia@example.invalid",
    "adres-miejscowosc": "Nowy Targ", "adres-nr_dzialki": "1704/8",
    "adres-identyfikator_dzialki": "121101_1.0001.1704/8",
    "nier-gmina": "Nowy Targ", "egibw-wnioskodawca": "Julia Kontrolna\nul. Fikcyjna 16/3\n34-400 Nowy Targ",
    "egibw-data": "20.11.2026", "egibw-powiat": "nowotarski", "egibw-gmina": "Nowy Targ",
    "egibw-obreb": "Nowy Targ", "egibw-dzialki": "1704/8", "egibw-kontakt_osoba": "Julia Kontrolna",
    "egibw-email": "julia@example.invalid", "egibw-przedmiot": ["wypis_grunty", "wyrys"],
    "egibw-uzasadnienie": ["wlasciciel"], "egibw-postac": ["papierowa"],
    "egibw-odbior": ["osobiscie"],
}


def generuj(form):
    with app.test_client() as c:
        response = c.post("/generuj", data=form)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.namelist() == ["EGiB_Wypis_Wyrys_Kontrolna.docx"]
        return Document(io.BytesIO(z.read(z.namelist()[0])))


def tekst(d):
    return "\n".join([p.text for p in d.paragraphs] + [p.text for t in d.tables for row in t.rows for cell in row.cells for p in cell.paragraphs])


def runy(d):
    return [r for p in d.paragraphs for r in p.runs] + [r for t in d.tables for row in t.rows for cell in row.cells for p in cell.paragraphs for r in p.runs]


def test_wypis_wyrys_przenosi_dane_i_zaznacza_wybory():
    d = generuj(BASE)
    t = tekst(d)
    for fragment in ["Julia Kontrolna", "ul. Fikcyjna 16/3", "Nowy Targ", "1704/8", "GK.6621.", "Wydział Geodezji, Katastru i Kartografii"]:
        assert fragment in t
    assert "{{" not in t
    choices = {r.style.name: r.text for r in runy(d) if r.style.name.startswith("EGIBW_")}
    assert choices["EGIBW_PRZEDMIOT_WYPIS_GRUNTY"] == "☒"
    assert choices["EGIBW_PRZEDMIOT_WYRYS"] == "☒"
    assert choices["EGIBW_PRZEDMIOT_UPROSZCZONY"] == "☐"
    assert choices["EGIBW_UZASADNIENIE_WLASCICIEL"] == "☒"
    assert choices["EGIBW_POSTAC_PAPIEROWA"] == "☒"
    assert choices["EGIBW_ODBIOR_OSOBISCIE"] == "☒"


@pytest.mark.parametrize("zmiany,blad", [
    ({"egibw-przedmiot": []}, "zaznacz przedmiot"),
    ({"egibw-dzialki": "abc"}, "sprawdź numery działek"),
    ({"egibw-data": "31.02.2026"}, "prawidłową datę"),
    ({"egibw-uzasadnienie": ["interes_prawny"]}, "opisz akt prawny"),
    ({"egibw-odbior": ["wysylka_inny"]}, "podaj adres wysyłki"),
    ({"egibw-uzasadnienie": []}, "wskaż podstawę dostępu"),
    ({"egibw-postac": []}, "wybierz postać dokumentów"),
])
def test_walidacja_wniosku_wypis_wyrys(zmiany, blad):
    with app.test_client() as c:
        response = c.post("/generuj", data=BASE | zmiany)
    assert response.status_code == 400
    assert blad in response.get_data(as_text=True)
