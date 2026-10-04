import json
from pathlib import Path

import pytest

from app.parser_obiegowki import (odczytaj_obiegowke, rozbierz_adres_inwestycji, rozbierz_inwestorow,
                                  zgadnij_plec)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def wynik():
    return odczytaj_obiegowke(FIXTURES / "obiegowka_przyklad.docx")


@pytest.fixture(scope="module")
def oczekiwane():
    return json.loads((FIXTURES / "obiegowka_PB_oczekiwane.json").read_text(encoding="utf-8"))


def test_pola_proste(wynik, oczekiwane):
    for pole in ["nazwa_inwestycji", "kategoria_obiektu", "data_opracowania", "zawartosc_projektu",
                 "projektant_glowny"]:
        assert wynik[pole] == oczekiwane[pole], pole


def test_jednostka_projektowa(wynik, oczekiwane):
    for klucz, wartosc in oczekiwane["jednostka_projektowa"].items():
        assert wynik["jednostka_projektowa"][klucz] == wartosc, klucz


def test_adres_inwestycji(wynik, oczekiwane):
    for klucz, wartosc in oczekiwane["adres_inwestycji"].items():
        assert wynik["adres_inwestycji"][klucz] == wartosc, klucz


def test_inwestor(wynik, oczekiwane):
    assert len(wynik["inwestorzy"]) == len(oczekiwane["inwestorzy"])
    for odczytany, wzor in zip(wynik["inwestorzy"], oczekiwane["inwestorzy"]):
        for klucz, wartosc in wzor.items():
            assert odczytany[klucz] == wartosc, klucz
        assert odczytany["plec"] == "M"


def test_teryt_nieruchomosci_i_inwestora(wynik, oczekiwane):
    assert wynik["nieruchomosc"] == oczekiwane["teryt"]
    for klucz, wartosc in oczekiwane["teryt"].items():
        assert wynik["inwestorzy"][0][klucz] == wartosc


def test_zespol_projektowy(wynik, oczekiwane):
    zespol = wynik["zespol_projektowy"]
    assert len(zespol) == len(oczekiwane["zespol_projektowy"])
    for odczytany, wzor in zip(zespol, oczekiwane["zespol_projektowy"]):
        assert (odczytany["specjalnosc"], odczytany["rola"], odczytany["osoba"]) == \
               (wzor["specjalnosc"], wzor["rola"], wzor["osoba"])
        assert wzor["nr_uprawnien"] in odczytany["uprawnienia"]


def test_ostrzezenia_o_niespojnosci(wynik, oczekiwane):
    pola = sorted(o["pole"] for o in wynik["ostrzezenia"])
    assert pola == sorted(oczekiwane["oczekiwane_ostrzezenia_dla_pol"])
    assert "PROJEKT BUDOWLANY" in wynik["ostrzezenia"][0]["komunikat"]


def test_zrodla(wynik):
    assert wynik["zrodla"][:3] == ["PROJEKT ZAGOSPODAROWANIA TERENU", "PROJEKT BUDOWLANY", "OŚWIADCZENIE PROJEKTANTA"]
    assert len(wynik["zrodla"]) == 5


def test_kilku_inwestorow_wspolny_adres():
    osoby = rozbierz_inwestorow("Jan Kowalski i Anna Kowalska\nul. Polna 5/2\n34-700 Rabka-Zdrój")
    assert [o["imie_nazwisko"] for o in osoby] == ["Jan Kowalski", "Anna Kowalska"]
    assert [o["plec"] for o in osoby] == ["M", "K"]
    assert all((o["ulica"], o["nr_domu"], o["nr_lokalu"], o["kod_pocztowy"], o["miejscowosc"]) ==
               ("ul. Polna", "5", "2", "34-700", "Rabka-Zdrój") for o in osoby)


def test_kilku_inwestorow_osobne_adresy():
    osoby = rozbierz_inwestorow("Jan Kowalski\nul. Polna 5\n34-700 Rabka-Zdrój\n"
                                "Anna Nowak\nul. Długa 1\n32-400 Myślenice")
    assert [(o["imie_nazwisko"], o["ulica"], o["miejscowosc"]) for o in osoby] == [
        ("Jan Kowalski", "ul. Polna", "Rabka-Zdrój"), ("Anna Nowak", "ul. Długa", "Myślenice")]


def test_adres_wiejski_bez_ulicy():
    osoba = rozbierz_inwestorow("Jan Kowalski\nPcim 123\n32-432 Pcim")[0]
    assert (osoba["ulica"], osoba["nr_domu"], osoba["miejscowosc"]) == ("", "123", "Pcim")


def test_nie_rozdziela_wspolnego_nazwiska():
    assert [o["imie_nazwisko"] for o in rozbierz_inwestorow("Jan i Anna Kowalscy\nul. Polna 1\n34-700 Rabka-Zdrój")] \
        == ["Jan i Anna Kowalscy"]


def test_adres_inwestycji_z_ulica_i_dzialka_z_ukosnikiem():
    adres = rozbierz_adres_inwestycji("dz. ew. 1234/5\n121112_4.0001.1234/5\nRabka-Zdrój, ul. Polna 7a")
    assert (adres["nr_dzialki"], adres["identyfikator_dzialki"], adres["miejscowosc"], adres["ulica"],
            adres["nr_domu"]) == ("1234/5", "121112_4.0001.1234/5", "Rabka-Zdrój", "ul. Polna", "7a")


@pytest.mark.parametrize("osoba,plec", [("Anna Nowak", "K"), ("Jacek Nowak", "M"), ("Kuba Nowak", "M")])
def test_zgadywanie_plci(osoba, plec):
    assert zgadnij_plec(osoba) == plec
