"""PB-9: nowy i dotychczasowy inwestor, decyzja, załączniki, walidacja."""
import io
import zipfile

import pytest
from docx import Document

from app.main import app


BASE = {
    "dokumenty": "pb9", "wybor_potwierdzony": "tak",
    "inw-0-imie_nazwisko": "Krzysztof Testowy", "inw-0-miejscowosc": "Kraków",
    "inw-0-ulica": "ul. Przykładowa", "inw-0-nr_domu": "12", "inw-0-nr_lokalu": "4",
    "inw-0-kod_pocztowy": "30-001", "adres-miejscowosc": "Zakopane",
    "adres-ulica": "ul. Słoneczna", "adres-nr_domu": "8", "adres-kod_pocztowy": "34-500",
    "adres-nr_dzialki": "245/7", "adres-identyfikator_dzialki": "121701_1.0005.245/7",
    "pb9-0-dotychczasowy_inwestor": "Jan Poprzedni", "pb9-0-data_decyzji": "10.02.2025",
    "pb9-0-nr_decyzji": "12/2025", "pb9-0-znak_sprawy": "AB.6740.12.2025",
    "pb9-0-nazwa_zamierzenia": "Budowa budynku mieszkalnego jednorodzinnego",
}


def pobierz(form):
    with app.test_client() as c:
        response = c.post("/generuj", data=form)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.namelist() == ["PB-9_Krzysztof_Testowy.docx"]
        return Document(io.BytesIO(z.read(z.namelist()[0])))


def tekst(d):
    return "\n".join(p.text for p in d.paragraphs)


def test_pb9_dane_stron_decyzja_i_zalaczniki():
    d = pobierz(BASE | {"pb9-0-zal-oswiadczenie": "tak", "pb9-0-zal-zgoda": "tak"})
    t = tekst(d)
    for s in ["PB-9", "Krzysztof Testowy", "Jan Poprzedni", "Starosta Nowotarski", "10.02.2025", "12/2025", "AB.6740.12.2025", "Budowa budynku mieszkalnego jednorodzinnego", "Przejmuję na siebie warunki", "Zgoda dotychczasowego inwestora", "nie jest wymagana"]:
        assert s in t
    assert "{{" not in t
    runs = [r for p in d.paragraphs for r in p.runs]
    assert next(r for r in runs if r.style.name == "PB9_ZAL_zgoda").text.startswith("☒")
    assert next(r for r in runs if r.style.name == "PB9_ZAL_oplata").text.startswith("☐")


def test_pb9_pelnomocnik_i_adres_korespondencyjny():
    d = pobierz(BASE | {"pb9-0-typ_pelnomocnika": "pelnomocnik", "pb9-0-proxy-imie_nazwisko": "Anna Przykładowa", "pb9-0-proxy-miejscowosc": "Nowy Targ", "pb9-0-koresp-miejscowosc": "Kraków"})
    t = tekst(d)
    assert "Anna Przykładowa" in t and "Kraków" in t
    runs = [r for p in d.paragraphs for r in p.runs]
    assert next(r for r in runs if r.style.name == "PB9_TYP_pelnomocnik").text.count("☒") == 1
    assert next(r for r in runs if r.style.name == "PB9_TYP_do_doreczen").text.count("☐") == 1


@pytest.mark.parametrize("zmiany, blad", [
    ({"pb9-0-dotychczasowy_inwestor": ""}, "dotychczasowego inwestora"),
    ({"pb9-0-data_decyzji": "31.02.2025"}, "poprawną datą"),
    ({"pb9-0-data_decyzji": "2025-02-10"}, "format DD.MM.RRRR"),
    ({"pb9-0-nr_decyzji": ""}, "numer"),
    ({"pb9-0-typ_pelnomocnika": "do_doreczen"}, "podaj imię i nazwisko"),
])
def test_bledne_dane_pb9_nie_przechodza(zmiany, blad):
    with app.test_client() as c:
        response = c.post("/generuj", data=BASE | zmiany)
    assert response.status_code == 400 and blad in response.get_data(as_text=True)
