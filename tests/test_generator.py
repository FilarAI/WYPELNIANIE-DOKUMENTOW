import copy
import io
from pathlib import Path

import docx
import pytest

from app.generator import generuj_dokumenty, kontekst_pelnomocnictwa
from app.parser_obiegowki import odczytaj_obiegowke

FIXTURES = Path(__file__).parent / "fixtures"


def tekst(zawartosc: bytes) -> str:
    return "\n".join(p.text for p in docx.Document(io.BytesIO(zawartosc)).paragraphs)


@pytest.fixture
def dane():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_przyklad.docx")
    d["data_pelnomocnictwa"] = "04.10.2026"
    return d


def test_jeden_inwestor(dane):
    pliki = generuj_dokumenty(dane)
    assert list(pliki) == ["Pelnomocnictwo_Kowalski.docx", "PB-5_Kowalski_Jan.docx"]

    pelnomocnictwo = tekst(pliki["Pelnomocnictwo_Kowalski.docx"])
    for fragment in ["Rabka-Zdrój 04.10.2026", "Ja Jan Kowalski", "zamieszkały: ul. Przykładowa 1, 32-400 Myślenice",
                     "udzielam pełnomocnictwa", "do mnie jako inwestora", "w moim imieniu",
                     "realizacją inwestycji „NADBUDOWA", "Myślenice ul. Przykładowa 1 dz. ew. 1358", "Upoważniam"]:
        assert fragment in pelnomocnictwo, fragment
    assert "……………………………………\nPodpis" in pelnomocnictwo
    assert "{{" not in pelnomocnictwo and "Adaś" not in pelnomocnictwo

    pb5 = tekst(pliki["PB-5_Kowalski_Jan.docx"])
    for fragment in ["Imię i nazwisko lub nazwa: Jan Kowalski",
                     "Kraj: Polska Województwo: małopolskie Powiat: myślenicki Gmina: Myślenice",
                     "Ulica: Przykładowa Nr domu: 1",
                     "Miejscowość: Myślenice Kod pocztowy: 32-400 Poczta: Myślenice",
                     "Identyfikator działki ewidencyjnej3): 120903_4.0002.1358"]:
        assert fragment in pb5, fragment
    assert "{{" not in pb5
    # Bez zaznaczenia opcji dane osoby upoważnionej zostają do uzupełnienia ręcznie.
    assert "Bartłomiej Filar" not in pb5


def test_dwoch_inwestorow_i_osoba_upowazniona(dane):
    druga = copy.deepcopy(dane["inwestorzy"][0]) | {"imie_nazwisko": "Anna Kowalska", "plec": "K"}
    dane["inwestorzy"].append(druga)
    dane["upowazniony_w_pb5"] = True
    pliki = generuj_dokumenty(dane)
    assert list(pliki) == ["Pelnomocnictwo_Kowalski_Kowalska.docx", "PB-5_Kowalski_Jan.docx",
                           "PB-5_Kowalska_Anna.docx"]

    pelnomocnictwo = tekst(pliki["Pelnomocnictwo_Kowalski_Kowalska.docx"])
    for fragment in ["My Jan Kowalski i Anna Kowalska", "zamieszkali:", "udzielamy pełnomocnictwa",
                     "do nas jako inwestorów", "w naszym imieniu", "Upoważniamy"]:
        assert fragment in pelnomocnictwo, fragment

    # Osobna linia podpisu dla każdego inwestora.
    assert "……………………………………\nJan Kowalski" in pelnomocnictwo
    assert "……………………………………\nAnna Kowalska" in pelnomocnictwo

    pb5 = tekst(pliki["PB-5_Kowalska_Anna.docx"])
    assert "Imię i nazwisko lub nazwa: Anna Kowalska" in pb5
    assert "Imię i nazwisko lub nazwa: Bartłomiej Filar" in pb5
    assert "Powiat: nowotarski Gmina: Rabka-Zdrój" in pb5


def test_formy_dla_kobiety(dane):
    dane["inwestorzy"][0] |= {"imie_nazwisko": "Anna Kowalska", "plec": "K"}
    assert kontekst_pelnomocnictwa(dane)["zamieszkaly"] == "zamieszkała"


def test_puste_pola_zostaja_kropkowane(dane):
    dane["inwestorzy"][0]["kod_pocztowy"] = ""
    pb5 = tekst(generuj_dokumenty(dane)["PB-5_Kowalski_Jan.docx"])
    assert "Kod pocztowy: …………………… Poczta: Myślenice" in pb5


def test_znaki_specjalne_nie_psuja_dokumentu(dane):
    dane["nazwa_inwestycji"] = "BUDOWA <GARAŻU> & WIATY"
    pelnomocnictwo = tekst(next(iter(generuj_dokumenty(dane).values())))
    assert "BUDOWA <GARAŻU> & WIATY" in pelnomocnictwo
