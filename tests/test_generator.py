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


def test_pelna_obiegowka_testowa_wypelnia_wszystkie_pola():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_testowa_pelna.docx")
    d["data_pelnomocnictwa"] = "04.10.2026"
    assert d["ostrzezenia"] == []
    pliki = generuj_dokumenty(d)
    pb5 = tekst(pliki["PB-5_Testowy_Krzysztof.docx"])
    sekcje_wypelniane = pb5.split("1. DANE INWESTORA")[1].split("2. DANE OSOBY")[0] + \
        pb5.split("3. DANE NIERUCHOMOŚCI")[1].split("Liczba stron")[0]
    assert "……" not in sekcje_wypelniane
    for fragment in ["Ulica: Przykładowa Nr domu: 12 Nr lokalu: 4",
                     "Kraj: Polska Województwo: małopolskie Powiat: Kraków Gmina: Kraków",
                     "Powiat: tatrzański Gmina: Zakopane", "Ulica: Słoneczna Nr domu: 8",
                     "Miejscowość: Zakopane Kod pocztowy: 34-500", "121701_1.0005.245/7"]:
        assert fragment in pb5, fragment
    pelnomocnictwo = tekst(pliki["Pelnomocnictwo_Testowy.docx"])
    assert "Zakopane ul. Słoneczna 8 dz. ew. 245/7" in pelnomocnictwo
    assert "zamieszkały: ul. Przykładowa 12/4, 30-001 Kraków" in pelnomocnictwo


def test_obiegowka_testowa_dwoje_inwestorow():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_testowa_dwoje_inwestorow.docx")
    assert [i["imie_nazwisko"] for i in d["inwestorzy"]] == ["Marek Przykładny", "Ewa Przykładna"]
    assert d["ostrzezenia"] == []
    assert list(generuj_dokumenty(d | {"data_pelnomocnictwa": "04.10.2026"})) == [
        "Pelnomocnictwo_Przykladny_Przykladna.docx", "PB-5_Przykladny_Marek.docx", "PB-5_Przykladna_Ewa.docx"]


def test_obiegowka_testowa_tylko_strona_PB():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_testowa_tylko_PB.docx")
    assert d["zrodla"] == ["PROJEKT BUDOWLANY"] and d["ostrzezenia"] == []
    # Miejscowość działki nie jest podana w obiegówce – wynika z identyfikatora TERYT (121701_1 = miasto Zakopane).
    adres = d["adres_inwestycji"]
    assert (adres["nr_dzialki"], adres["ulica"], adres["miejscowosc"]) == ("245/7", "", "Zakopane")
    pliki = generuj_dokumenty(d | {"data_pelnomocnictwa": "04.10.2026"})
    pb5 = tekst(pliki["PB-5_Testowy_Krzysztof.docx"])
    assert "Ulica: …………………… Nr domu: ……………………" in pb5
    assert "Miejscowość: Zakopane Kod pocztowy: ……………………" in pb5
    assert "Powiat: tatrzański Gmina: Zakopane" in pb5
    assert "Zakopane dz. ew. 245/7" in tekst(pliki["Pelnomocnictwo_Testowy.docx"])


def test_obiegowka_testowa_wies_kobieta():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_testowa_wies_kobieta.docx")
    assert d["ostrzezenia"] == []
    inw = d["inwestorzy"][0]
    assert (inw["imie_nazwisko"], inw["plec"], inw["ulica"], inw["nr_domu"], inw["miejscowosc"], inw["gmina"]) == \
           ("Anna Testowa", "K", "", "123", "Pcim", "Pcim")
    pliki = generuj_dokumenty(d | {"data_pelnomocnictwa": "04.10.2026"})
    pelnomocnictwo = tekst(pliki["Pelnomocnictwo_Testowa.docx"])
    assert "zamieszkała: Pcim 123, 32-432 Pcim" in pelnomocnictwo
    assert "Pcim 123 dz. ew. 555/1" in pelnomocnictwo
    pb5 = tekst(pliki["PB-5_Testowa_Anna.docx"])
    assert "Ulica: …………………… Nr domu: 123" in pb5
    assert "Powiat: myślenicki Gmina: Pcim" in pb5


def test_obiegowka_testowa_niespojna():
    d = odczytaj_obiegowke(FIXTURES / "obiegowka_testowa_niespojna.docx")
    assert sorted(o["pole"] for o in d["ostrzezenia"]) == ["data_opracowania", "inwestor"]
    # Dane bierzemy ze strony „PROJEKT BUDOWLANY”, a różnice są tylko zgłaszane.
    assert d["inwestorzy"][0]["imie_nazwisko"] == "Krzysztof Testowy"
    assert d["data_opracowania"] == "MARZEC 2026"


def _maly_png(szerokosc: int, wysokosc: int) -> bytes:
    """Minimalny, poprawny plik PNG (szary prostokąt) – bez zależności od Pillow."""
    import struct
    import zlib

    def blok(typ, dane):
        return struct.pack(">I", len(dane)) + typ + dane + struct.pack(">I", zlib.crc32(typ + dane) & 0xFFFFFFFF)

    wiersze = b"".join(b"\x00" + b"\xc0" * szerokosc for _ in range(wysokosc))
    return (b"\x89PNG\r\n\x1a\n" + blok(b"IHDR", struct.pack(">IIBBBBB", szerokosc, wysokosc, 8, 0, 0, 0, 0))
            + blok(b"IDAT", zlib.compress(wiersze)) + blok(b"IEND", b""))


def test_baner_w_naglowku_pelnomocnictwa(tmp_path, monkeypatch, dane):
    import app.generator as generator
    import narzedzia.zbuduj_szablony as zbuduj

    grafika = tmp_path / "naglowek_filar.png"
    grafika.write_bytes(_maly_png(248, 36))
    szablon = tmp_path / "pelnomocnictwo.docx"
    assert zbuduj.pelnomocnictwo(cel=szablon, grafika=grafika) is True
    monkeypatch.setattr(generator, "SZABLON_PELNOMOCNICTWA", szablon)

    wynik = docx.Document(io.BytesIO(generuj_dokumenty(dane)["Pelnomocnictwo_Kowalski.docx"]))
    naglowek = wynik.sections[0].header
    assert naglowek._element.xpath(".//pic:pic")  # obraz zachowany po wypełnieniu przez docxtpl
    szerokosc_banera = int(naglowek._element.xpath(".//wp:extent/@cx")[0])
    assert abs(szerokosc_banera - wynik.sections[0].page_width) < 10_000  # baner na całą szerokość kartki
    stopka = wynik.sections[0].footer.paragraphs[0].text
    assert stopka.startswith("FILAR-USŁUGI adres: ul. Sądecka 33h/11") and "812, e-mail:" in stopka


def test_pelnomocnictwo_bez_grafiki(tmp_path):
    import narzedzia.zbuduj_szablony as zbuduj

    szablon = tmp_path / "pelnomocnictwo.docx"
    assert zbuduj.pelnomocnictwo(cel=szablon, grafika=tmp_path / "brak.png") is False
    assert not docx.Document(szablon).sections[0].header._element.xpath(".//pic:pic")


def test_nr_lokalu_kreska_gdy_adres_bez_mieszkania(dane):
    pb5 = tekst(generuj_dokumenty(dane)["PB-5_Kowalski_Jan.docx"])
    assert "Ulica: Przykładowa Nr domu: 1 Nr lokalu: –" in pb5


def test_nr_lokalu_podany(dane):
    dane["inwestorzy"][0]["nr_lokalu"] = "7"
    assert "Nr domu: 1 Nr lokalu: 7" in tekst(generuj_dokumenty(dane)["PB-5_Kowalski_Jan.docx"])


def test_nr_lokalu_kropki_gdy_brak_adresu(dane):
    dane["inwestorzy"][0] |= {"ulica": "", "nr_domu": "", "nr_lokalu": ""}
    pb5 = tekst(generuj_dokumenty(dane)["PB-5_Kowalski_Jan.docx"])
    assert "Ulica: …………………… Nr domu: …………………… Nr lokalu: ……………………" in pb5
