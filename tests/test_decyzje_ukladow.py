"""Różne układy decyzji o pozwoleniu na budowę (dane fikcyjne, układ i błędy OCR jak w prawdziwych skanach)."""
import io

from docx import Document

from app.scalanie_zrodel import odczytaj_zestaw


def docx(*linie):
    d = Document()
    for linia in linie:
        d.add_paragraph(linia)
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


# Nowy Targ 2020: zdanie „udzielam pozwolenia” przełamane, „dla:” w osobnej linii,
# parametry w kolumnach bez indeksów górnych (OCR: „m” zamiast „m3”), uszkodzony nagłówek.
NOWY_TARG_2020 = docx(
    "STAR", "ui. Boleslaw", "WOTARSKI", "Wstydliwego 14", "Y TARG",
    "Nasz znak: BA.6740.1.1000.2020.MT", "Nowy Targ, 14.10.2020 r.", "DECYZJA nr 1300/ 2020",
    "Na podstawie art. 28, art. 33 ust. 1 ustawy z dnia 7 lipca 1994 r. - Prawo budowlane",
    "rozpatrzeniu wniosku złożonego w dniu 28.07.2020 r.,",
    "ZATWIERDZAM PROJEKT BUDOWLANY') I UDZIELAM POZWOLENIA NA", 'BUDOWE"', "dla:",
    "Państwa Tomasza i Ewy Testowskich, zam. ul. Polna 7c, 34-700 Rabka-Zdrój",
    "reprezentowanych przez Panią Małgorzatę Jachimowską-Filar, ul. Sądecka 33h/11, 34-700 Rabka-Zdrój",
    "obejmujące:", "budynek mieszkalny jednorodzinny z garażem wbudowanym",
    "wraz z urządzeniami budowlanymi i infrastrukturą techniczną:",
    "na działce nr ewid.: 555 w miejscowości Rabka-Zdrój obręb ew. 0002 Rabka -Słone jedn. ewid. 121112_4",
    "Rabka-Zdrój.", "parametry obiektu:", "- kubatura -", "- pow. zabudowy-", "- pow. użytkowa-", "- ogrzewanie-",
    "450,10 m", "110,50 m", "80,20 m", "gazowe", "kategoria obiektu budowlanego -",
    "zgodnie z projektem budowlanym opracowanym przez:", "UZASADNIENIE",
    "Wnioskiem, złożonym w dniu 28.07.2020 r. Państwo Tomasz i Ewa Testowski, zam. jw.",
    "Inwestor jest obowiązany zgłosić Staroście Nowotarskiemu zakończenie budowy.",
)

# Nowy Targ 2026: jedna inwestorka w dopełniaczu, mianownik w uzasadnieniu, identyfikator
# przełamany („121112.” / „_4”), dwa rodzaje budynków w tabeli parametrów, data wniosku w sentencji.
NOWY_TARG_2026 = docx(
    "STAROSTA NOWOTARSKI", "ul. Bolesława Wstydliwego 14", "34-400 Nowy Targ",
    "Nasz znak BA.6740.1.800.2024.ID", "Nowy Targ, dnia 06.02.2026r.", "DECYZJA NR 120/2026",
    "po rozpatrzeniu wniosku Inwestora z dnia 03.06.2024r., z datą wpływu 10.07.2024r.,",
    "ZATWIERDZAM PROJEKT ZAGOSPODAROWANIA TERENU", "ORAZ PROJEKT ARCHITEKTONICZNO-BUDOWLANY",
    "TUDZIELAM POZWOLENIA NA BUDOWĘ",
    "dla Pani Agnieszki Próbnej, zam. ul. Leśna ба, 34-700 Rabka-Zdrój,",
    "reprezentowanej przez Pelnomocnika Panią Małgorzatę Jachimowską- Filar,", "obejmujące:",
    "budowę budynku mieszkalnego jednorodzinnego oraz dwóch budynków letniskowych",
    "z urządzeniami budowlanymi i infrastrukturą techniczną:",
    "na działkach nr ewid.: 1101, 1102 w miejscowości Rabka-Zdrój, obręb ew. 0002 Rabka-",
    "Slone, jedn. ewid. 121112.", "_4 Rabka-Zdrój,", "o następujących parametrach technicznych:",
    "budynek mieszkalny", "jednorodzinny", "budynek letniskowy ozn. nr 2, 3", "(dane dla jednego budynku)",
    "kategoria obiektu budowlanego", "- kubatura", "- powierzchnia zabudowy", "- powierzchnia użytkowa",
    "- ilość lokali mieszkalnych", "- ilość izb mieszkalnych", "- ogrzewanie",
    "900,00 m", "140,10 m2", "200,40 m?", "400,00", "61,20", "99,15", "6", "kocioł na pellet", "3",
    "projekt zagospodarowania terenu opracowany przez:", "UZASADNIENIE",
    "Inwestor - Pani Agnieszka Próbna, zam. ul. Leśna 6a, 34-700 Rabka-Zdrój,",
    "reprezentowana przez Pelnomocnika Panią Małgorzatę Jachimowską- Filar, wnioskiem z dnia",
)

# Limanowa 2018: mocno zaszumiony OCR, parametry w jednej linii, obręb nazwą (bez numeru TERYT).
LIMANOWA_DANE = (
    "SIANUSIA LIMANUWSKI", "34-600 Limanowa", "BA.0Z.6740.1.10.2018", "(ne rejestru orgenu wydajecago decyme)",
    "Mazana Do/na. 27 SZerM C 2018 oku", "DECYZJA NR 160/2018",
    "po rozpatrzeniu wniosku o pozwolenie na budowę z 15.05.2018 roku,",
    "Zatwlerdzam projekt budowlany l udzielam pozwolenla na budową dia:",
    "Inwestora: Pani Maril Próbka, zam. ul. Szkolna 3, 34-730 Mszana Dolna", "obelmulace:",
    "nadbudowę i przebudowę budynku mieszkalnego jednorodzinnego.",
    "Adres zamierzenia budowlanego: dzialka ew. nr 2001, 2000/3 obręb Gronoszowa, Jednostka ewidencyjna Mszana Dolna,",
    "Kategoria obiektu budowlanego: 1",
    "Budynek o danych lechnicznych: pow. zabudowy - 100,90 m?, pow. ubytkowa - 300,60 m?, kubatura - 1400,00 ml.",
    "Uzasadnionle", "15.05.2018 roku, inwestor Pani Maria Próbka, złożyla wniosek o wydanie pozwolenia na budowę",
    "Z up. STAROSTY LIMANOWSKIEGO",
)
LIMANOWA_2018 = docx(*LIMANOWA_DANE)


def test_nowy_targ_2020_przelamane_zdanie_i_dopelniacz():
    d = odczytaj_zestaw([("decyzja", "a.docx", NOWY_TARG_2020)])
    z = d["zakonczenie"]
    assert (z["pozwolenie_numer"], z["pozwolenie_znak"], z["pozwolenie_data"], z["pozwolenie_organ"]) == \
        ("1300/2020", "BA.6740.1.1000.2020.MT", "14.10.2020", "Starostę Nowotarskiego")
    assert [i["imie_nazwisko"] for i in d["inwestorzy"]] == ["Tomasz Testowski", "Ewa Testowski"]
    inw = d["inwestorzy"][0]
    assert (inw["ulica"], inw["nr_domu"], inw["kod_pocztowy"], inw["miejscowosc"]) == ("ul. Polna", "7c", "34-700", "Rabka-Zdrój")
    a = d["adres_inwestycji"]
    assert (a["nr_dzialki"], a["identyfikator_dzialki"], a["miejscowosc"]) == ("555", "121112_4.0002.555", "Rabka-Zdrój")
    assert d["nazwa_inwestycji"] == "Budynek mieszkalny jednorodzinny z garażem wbudowanym"
    assert (z["kubatura_mieszkalna"], z["pow_zabudowy_mieszkalna"], z["pow_uzytkowa_mieszkalna"]) == ("450,10", "110,50", "80,20")


def test_nowy_targ_2026_data_decyzji_nie_wniosku_i_kilka_budynkow():
    d = odczytaj_zestaw([("decyzja", "b.docx", NOWY_TARG_2026)])
    z = d["zakonczenie"]
    assert (z["pozwolenie_numer"], z["pozwolenie_znak"], z["pozwolenie_data"]) == ("120/2026", "BA.6740.1.800.2024.ID", "06.02.2026")
    assert [i["imie_nazwisko"] for i in d["inwestorzy"]] == ["Agnieszka Próbna"]
    assert d["inwestorzy"][0]["plec"] == "K" and d["inwestorzy"][0]["nr_domu"] == "6a"
    assert [x["identyfikator"] for x in d["dzialki_do_wyboru"]] == ["121112_4.0002.1101", "121112_4.0002.1102"]
    assert d["nazwa_inwestycji"].startswith("Budowa budynku mieszkalnego jednorodzinnego oraz dwóch")
    assert (z["kubatura_mieszkalna"], z["pow_zabudowy_mieszkalna"], z["pow_uzytkowa_mieszkalna"]) == ("900,00", "140,10", "200,40")
    assert "liczba_izb" not in z and "liczba_mieszkan" not in z  # przy kilku budynkach nie zgadujemy
    assert any("kilka budynków" in o["komunikat"] for o in d["ostrzezenia"])


def test_limanowa_zaszumiony_ocr():
    d = odczytaj_zestaw([("decyzja", "c.docx", LIMANOWA_2018)])
    z = d["zakonczenie"]
    assert (z["pozwolenie_numer"], z["pozwolenie_znak"], z["pozwolenie_organ"]) == ("160/2018", "BA.0Z.6740.1.10.2018", "Starostę Limanowskiego")
    assert [i["imie_nazwisko"] for i in d["inwestorzy"]] == ["Maria Próbka"]
    assert d["inwestorzy"][0]["kod_pocztowy"] == "34-730"
    assert d["adres_inwestycji"]["nr_dzialki"] == "2001, 2000/3"  # bez numeru obrębu nie da się złożyć identyfikatora
    assert d["nazwa_inwestycji"] == "Nadbudowa i przebudowa budynku mieszkalnego jednorodzinnego"
    assert (z["kubatura_mieszkalna"], z["pow_zabudowy_mieszkalna"], z["pow_uzytkowa_mieszkalna"]) == ("1400,00", "100,90", "300,60")


def test_pelnomocnik_nie_jest_inwestorem():
    d = odczytaj_zestaw([("decyzja", "b.docx", NOWY_TARG_2026)])
    assert all("Jachimowsk" not in i["imie_nazwisko"] for i in d["inwestorzy"])


def test_zniekształcona_miejscowosc_z_tego_samego_kodu_w_dokumencie():
    # OCR zepsuł nazwę w sentencji, ale lista „Otrzymują” podaje ją poprawnie przy tym samym kodzie.
    linie = [x.replace("34-730 Mszana Dolna", "34-730 Mrna Dol a sand") for x in LIMANOWA_DANE]
    d = odczytaj_zestaw([("decyzja", "c.docx", docx(*linie, "Otrzymują:", "1. Pani Maria Próbka, zam. ul. Szkolna 3, 34-730 Mszana Dolna."))])
    inw = d["inwestorzy"][0]
    assert (inw["miejscowosc"], inw["poczta"], inw["gmina"]) == ("Mszana Dolna", "Mszana Dolna", "Mszana Dolna")
    assert not any("przyjęto" in o["komunikat"] for o in d["ostrzezenia"])  # pewne – bez ostrzeżenia


def test_zniekształcona_miejscowosc_bez_drugiego_wystapienia_to_propozycja():
    linie = [x.replace("34-730 Mszana Dolna", "34-730 Mszana Doina") for x in LIMANOWA_DANE]
    d = odczytaj_zestaw([("decyzja", "c.docx", docx(*linie))])
    assert d["inwestorzy"][0]["miejscowosc"] == "Mszana Dolna"
    assert any("„Mszana Doina”, przyjęto „Mszana Dolna”" in o["komunikat"] for o in d["ostrzezenia"])


def test_nieczytelna_miejscowosc_nie_jest_zgadywana():
    from app import teryt
    assert teryt.popraw_miejscowosc("Mrna Dol a sand") == ("Mrna Dol a sand", False)  # Mszana Dolna ≈ Tarnawa Dolna
    assert teryt.popraw_miejscowosc("Rabka-Zdrój", "34-700") == ("Rabka-Zdrój", True)
