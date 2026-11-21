"""PB-1: wniosek o pozwolenie na budowę, pola, wybory i walidacja."""
import io
import re
import zipfile
from pathlib import Path

import pytest
from docx import Document

from app.main import app

BASE = {
    "dokumenty": "pb1", "wybor_potwierdzony": "tak",
    "inw-0-imie_nazwisko": "Krzysztof Testowy", "inw-0-miejscowosc": "Kraków",
    "inw-0-ulica": "ul. Przykładowa", "inw-0-nr_domu": "12", "inw-0-nr_lokalu": "4",
    "inw-0-kod_pocztowy": "30-001", "inw-0-wojewodztwo": "małopolskie",
    "inw-0-powiat": "krakowski", "inw-0-gmina": "Zielonki",
    "adres-miejscowosc": "Zakopane", "adres-ulica": "ul. Słoneczna",
    "adres-nr_domu": "8", "adres-kod_pocztowy": "34-500",
    "adres-nr_dzialki": "245/7", "adres-identyfikator_dzialki": "121701_1.0005.245/7",
    "pb1-nazwa": "Budowa budynku mieszkalnego jednorodzinnego",
    "pb1-rodzaje": "budowa",
}


def pobierz(form):
    with app.test_client() as c: response = c.post("/generuj", data=form)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.namelist() == ["PB-1_Krzysztof_Testowy.docx"]
        return Document(io.BytesIO(z.read(z.namelist()[0])))


def tekst(d): return "\n".join(p.text for p in d.paragraphs)


def test_pb1_dane_nazwa_rodzaje_i_zalaczniki():
    d = pobierz(BASE | {"pb1-rodzaje": ["budowa", "rozbudowa"], "pb1-0-zal-projekt": "tak"})
    t = tekst(d)
    for s in ["PB-1", "Krzysztof Testowy", "Starosta Nowotarski", "34-500", "121701_1.0005.245/7", "Budowa budynku mieszkalnego jednorodzinnego", "Rozbudowa istniejącego obiektu budowlanego"]: assert s in t
    assert "{{" not in t
    runs = [r for p in d.paragraphs for r in p.runs]
    assert next(r for r in runs if r.style.name == "PB1_TYP_BUDOWA").text.startswith("☒")
    assert next(r for r in runs if r.style.name == "PB1_TYP_ROZBUDOWA").text.startswith("☒")
    assert next(r for r in runs if r.style.name == "PB1_ZAL_PROJEKT").text.startswith("☒")
    assert next(r for r in runs if r.style.name == "PB1_ZAL_OPLATA").text.startswith("☐")


def test_pb1_pelnomocnik_i_korespondencja():
    d = pobierz(BASE | {"pb1-0-typ_pelnomocnika": "do_doreczen", "pb1-0-proxy-imie_nazwisko": "Anna Przykładowa", "pb1-0-proxy-miejscowosc": "Nowy Targ", "pb1-0-koresp-miejscowosc": "Kraków"})
    t = tekst(d)
    assert "Anna Przykładowa" in t and "Nowy Targ" in t and "Kraków" in t
    runs = [r for p in d.paragraphs for r in p.runs]
    assert next(r for r in runs if r.style.name == "PB1_PEL_DO_DORECZEN").text.count("☒") == 1


def test_pb1_mozna_wybrac_w_podgladzie():
    fixture = Path(__file__).parent / "fixtures" / "obiegowka_testowa_pelna.docx"
    with app.test_client() as c:
        r = c.post("/wybierz-dokumenty", data={"plik_1": (io.BytesIO(fixture.read_bytes()), fixture.name), "typ_1": "obiegowka"}, content_type="multipart/form-data")
        assert r.status_code == 200
        token = re.search(rb'name="token" value="([^"]+)', r.data).group(1).decode()
        r = c.post("/podglad", data={"token": token, "dokumenty": "pb1"})
    assert r.status_code == 200 and "PB-1 — wniosek o pozwolenie na budowę" in r.get_data(as_text=True)


@pytest.mark.parametrize("zmiany,blad", [
    ({"pb1-nazwa": ""}, "podaj ogólną nazwę"),
    ({"pb1-rodzaje": "nieistniejacy"}, "poprawne rodzaje"),
    ({"pb1-rodzaje": ""}, "zaznacz co najmniej jeden"),
    ({"pb1-0-typ_pelnomocnika": "pelnomocnik"}, "podaj imię i nazwisko"),
])
def test_bledne_dane_pb1_nie_przechodza(zmiany, blad):
    with app.test_client() as c: response = c.post("/generuj", data=BASE | zmiany)
    assert response.status_code == 400 and blad in response.get_data(as_text=True)
