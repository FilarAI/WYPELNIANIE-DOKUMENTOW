"""Pola formularza potrzebne do dokumentów zakończenia budowy.

Obiegówka dostarcza inwestorów, nazwę inwestycji i adres działki. Pozostałe
informacje pochodzą od użytkownika; deklaracji i pomiarów nie zgadujemy.
"""
from __future__ import annotations

from app.konfiguracja import PELNOMOCNIK

POLA_TEKSTOWE = {
    "miejscowosc_sporzadzenia": 120,
    "data_sporzadzenia": 40,
    "pozwolenie_znak": 120,
    "pozwolenie_data": 40,
    "pozwolenie_organ": 200,
    "odstepstwa": 4000,
    "ep": 40,
    "u_sciany": 40,
    "u_dach": 40,
    "u_podloga": 40,
    "u_okna": 40,
    "u_drzwi": 40,
    "telefon_inwestora": 80,
    "liczba_budynkow": 40,
    "nr_budynku_sasiada": 80,
    "pozwolenie_uzytkowanie_data": 40,
    "pozwolenie_uzytkowanie_znak": 120,
    "data_zgloszenia_rozpoczecia": 40,
    "kubatura_mieszkalna": 40,
    "pow_zabudowy_mieszkalna": 40,
    "pow_uzytkowa_mieszkalna": 40,
    "pow_mieszkania": 40,
    "pow_uslugowa": 40,
    "pow_garazu": 40,
    "pow_calkowita": 40,
    "liczba_izb": 40,
    "liczba_mieszkan": 40,
    "kondygnacje_nadziemne": 40,
    "kondygnacje_podziemne": 40,
    "kubatura_innego": 40,
    "pow_zabudowy_innego": 40,
    "pow_uzytkowa_innego": 40,
    "kondygnacje_nadziemne_innego": 40,
    "kondygnacje_podziemne_innego": 40,
    "zbiornik_pojemnosc": 40,
    "inne_ogrzewanie": 120,
    "inne_zalaczniki": 500,
}

WYBORY = {
    "zgodnosc": [
        ("zgodnie", "Zgodnie z projektem i pozwoleniem"),
        ("odstepstwa", "Z nieistotnymi odstępstwami"),
    ],
    "teren_doprowadzony": [("tak", "Tak"), ("nie", "Nie")],
    "tereny_przylegle": [("tak", "Tak"), ("nie", "Nie"), ("nie_dotyczy", "Nie dotyczy")],
    "pomiary_powierzchni": [("tak", "Tak"), ("nie", "Nie")],
    "obiekt_nadaje_sie": [("tak", "Tak"), ("nie", "Nie")],
    "odbior_czesciowy": [("tak", "Tak"), ("nie", "Nie")],
    "forma_budownictwa": [
        ("indywidualne_wlasne", "Indywidualne — na własne potrzeby"),
        ("indywidualne_sprzedaz", "Indywidualne — na sprzedaż lub wynajem"),
        ("spoldzielcze", "Spółdzielcze"),
        ("sprzedaz_wynajem", "Na sprzedaż lub wynajem"),
        ("komunalne", "Komunalne"),
        ("spoleczne_czynszowe", "Społeczne czynszowe"),
        ("zakladowe", "Zakładowe"),
    ],
    "technologia": [
        ("tradycyjna", "Tradycyjna udoskonalona"),
        ("wielkoplytowa", "Wielkopłytowa"),
        ("wielkoblokowa", "Wielkoblokowa"),
        ("monolityczna", "Monolityczna"),
        ("kanadyjska", "Kanadyjska"),
        ("inna", "Inna"),
    ],
    "rodzaj_scian": [("ognioodporne", "Ognioodporne"), ("nieognioodporne", "Nieognioodporne"), ("nro", "NRO")],
    "kanalizacja": [
        ("miejska", "Kanalizacja miejska"),
        ("wiejska", "Kanalizacja wiejska"),
        ("zbiornik", "Szczelny zbiornik"),
        ("oczyszczalnia", "Oczyszczalnia przydomowa"),
    ],
    "pobor_wody": [
        ("studnia_kopana", "Studnia kopana"),
        ("studnia_wiercona", "Studnia wiercona"),
        ("wodociag_miejski", "Wodociąg miejski"),
        ("wodociag_wiejski", "Wodociąg wiejski"),
        ("wodociag_zagrodowy", "Wodociąg zagrodowy"),
        ("wodociag_indywidualny", "Wodociąg indywidualny"),
    ],
    "ogrzewanie": [
        ("olejowe", "Olejowe"),
        ("gazowe", "Gazowe"),
        ("opal_staly", "Opał stały"),
        ("pompa_ciepla", "Pompa ciepła"),
        ("inne", "Inne"),
    ],
    "gaz_sieciowy": [("tak", "Tak"), ("nie", "Nie")],
}

RODZAJE_OBIEKTU = [
    ("nowy", "Nowy"),
    ("rozbudowa", "Rozbudowa"),
    ("nadbudowa", "Nadbudowa"),
    ("przebudowa", "Przebudowa"),
    ("zmiana_uzytkowania", "Zmiana sposobu użytkowania"),
    ("adaptacja", "Adaptacja"),
    ("mieszkalny", "Mieszkalny"),
    ("niemieszkalny", "Niemieszkalny"),
]

ZALACZNIKI = [
    ("dziennik_budowy", "Dziennik budowy"),
    ("oswiadczenie_kierownika", "Oświadczenie kierownika budowy"),
    ("tereny_przylegle", "Oświadczenie o terenach przyległych"),
    ("przewody_kominowe", "Protokół przewodów kominowych"),
    ("instalacja_elektryczna", "Protokół instalacji elektrycznej"),
    ("instalacja_piorunochronna", "Protokół instalacji piorunochronnej"),
    ("instalacja_gazowa", "Protokół instalacji gazowej"),
    ("urzadzenia_ochrony_srodowiska", "Protokół urządzeń ochrony środowiska"),
    ("instalacje_technologiczne", "Protokół instalacji technologicznych"),
    ("przylacze_energetyczne", "Odbiór przyłącza energetycznego"),
    ("przylacze_wodociagowe", "Odbiór przyłącza wodociągowego"),
    ("przylacze_kanalizacyjne", "Odbiór przyłącza kanalizacyjnego"),
    ("przylacze_gazowe", "Odbiór przyłącza gazowego"),
    ("przylacze_cieplownicze", "Odbiór przyłącza ciepłowniczego"),
    ("inwentaryzacja_geodezyjna", "Inwentaryzacja geodezyjna powykonawcza"),
    ("pozwolenie_na_budowe", "Decyzja o pozwoleniu na budowę"),
    ("rysunki_ze_zmianami", "Rysunki ze zmianami"),
    ("opis_zmian", "Uzupełniający opis techniczny"),
    ("projekt_do_wgladu", "Projekt budowlany do wglądu"),
]


def adres_kierownika() -> str:
    return (f"ul. {PELNOMOCNIK['ulica']} {PELNOMOCNIK['nr_domu']}/"
            f"{PELNOMOCNIK['nr_lokalu']}, {PELNOMOCNIK['kod_pocztowy']} "
            f"{PELNOMOCNIK['miejscowosc']}")


def odczytaj_z_formularza(formularz) -> dict:
    """Czyta wyłącznie znane pola i odrzuca niepoprawne wybory."""
    wynik = {}
    for nazwa, limit in POLA_TEKSTOWE.items():
        wartosc = formularz.get(f"zak-{nazwa}", "").strip()
        if len(wartosc) > limit:
            raise ValueError("Jedno z pól zakończenia budowy jest zbyt długie.")
        wynik[nazwa] = wartosc

    wynik["kierownik_imie_nazwisko"] = PELNOMOCNIK["imie_nazwisko"]
    wynik["kierownik_adres"] = adres_kierownika()

    for nazwa, opcje in WYBORY.items():
        wartosc = formularz.get(f"zak-{nazwa}", "")
        if wartosc not in {"", *(kod for kod, _ in opcje)}:
            raise ValueError("Niepoprawny wybór w sekcji zakończenia budowy.")
        wynik[nazwa] = wartosc

    for nazwa, opcje in (("rodzaje_obiektu", RODZAJE_OBIEKTU), ("zalaczniki", ZALACZNIKI)):
        wybrane = formularz.getlist(f"zak-{nazwa}")
        dostepne = {kod for kod, _ in opcje}
        if len(wybrane) != len(set(wybrane)) or any(kod not in dostepne for kod in wybrane):
            raise ValueError("Niepoprawny wybór w sekcji zakończenia budowy.")
        wynik[nazwa] = wybrane

    return wynik
