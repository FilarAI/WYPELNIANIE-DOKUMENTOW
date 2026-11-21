"""Tworzy ręczny pakiet przykładów: dobry wynik i brakujące pole dla każdego dokumentu."""
from __future__ import annotations

import copy
import importlib
import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.main import app  # noqa: E402

COMMON = {
    "wybor_potwierdzony": "tak",
    "inw-0-imie_nazwisko": "Anna Testowa",
    "inw-0-plec": "K",
    "inw-0-ulica": "ul. Przykładowa",
    "inw-0-nr_domu": "12",
    "inw-0-nr_lokalu": "2",
    "inw-0-kod_pocztowy": "34-400",
    "inw-0-miejscowosc": "Nowy Targ",
    "adres-miejscowosc": "Nowy Targ",
    "adres-ulica": "ul. Testowa",
    "adres-nr_domu": "25",
    "adres-kod_pocztowy": "34-400",
    "adres-nr_dzialki": "1401/2",
    "adres-identyfikator_dzialki": "121101_1.0001.1401/2",
}

TEST_CASES = {
    "01_Pelnomocnictwo": ("pelnomocnictwo", "generator", "inw-0-imie_nazwisko", "", "brak inwestora"),
    "02_PB5": ("pb5", "generator", "inw-0-imie_nazwisko", "", "brak inwestora"),
    "03_Oswiadczenie_kierownika": ("oswiadczenie", "zakonczenie", "inw-0-imie_nazwisko", "", "brak inwestora"),
    "04_Zawiadomienie": ("zawiadomienie", "zakonczenie", "inw-0-imie_nazwisko", "", "brak inwestora"),
    "06_BA4": ("ba4", "test_ba4", "ba4-data_wniosku", "", "brak daty wniosku"),
    "07_EGiB_zmiany": ("egib", "test_egib", "egib-opis_zmian", "", "brak opisu zmian"),
    "09_Pelnomocnictwo_EGiB": ("pelnomocnictwo_egib", "test_pelnomocnictwo_egib", "pel-egib-0-pesel", "", "brak PESEL-u"),
    "10_EGiB_wypis_wyrys": ("egib_wypis", "test_egib_wypis", "egibw-przedmiot", [], "brak przedmiotu wniosku"),
    "11_PB2": ("pb2", "test_pb2", "pb2-roboty", "", "brak opisu robót"),
    "12_PB2a": ("pb2a", "test_pb2a", "pb2a-termin", "", "brak terminu"),
    "13_PB7": ("pb7", "test_pb7", "pb7-0-nr_decyzji", "", "brak numeru decyzji"),
    "14_PB9": ("pb9", "test_pb9", "pb9-0-dotychczasowy_inwestor", "", "brak dotychczasowego inwestora"),
    "15_PB1": ("pb1", "test_pb1", "pb1-nazwa", "", "brak ogólnej nazwy zamierzenia"),
    "16_OS6165": ("os616", "test_os616", "os616-dzialki", "", "brak numerów działek"),
    "18_Formularz_P": ("formularz_p", "test_formularz_p", "p-material", [], "brak rodzaju materiału"),
}

RODZAJE = {
    "01_Pelnomocnictwo": "Pełnomocnictwo",
    "02_PB5": "PB-5",
    "03_Oswiadczenie_kierownika": "Oświadczenie kierownika budowy",
    "04_Zawiadomienie": "Zawiadomienie o zakończeniu budowy",
    "06_BA4": "BA-4 — dziennik budowy / rozbiórki",
    "07_EGiB_zmiany": "Zgłoszenie zmian EGiB",
    "09_Pelnomocnictwo_EGiB": "Pełnomocnictwo EGiB",
    "10_EGiB_wypis_wyrys": "EGiB — wypis / wyrys",
    "11_PB2": "PB-2",
    "12_PB2a": "PB-2a",
    "13_PB7": "PB-7",
    "14_PB9": "PB-9",
    "15_PB1": "PB-1",
    "16_OS6165": "OŚ-6165",
    "18_Formularz_P": "Formularz P",
}


def baza(kod, mod):
    dane = copy.deepcopy(COMMON)
    dane["dokumenty"] = kod
    if mod == "generator":
        if kod == "pelnomocnictwo":
            dane["data_pelnomocnictwa"] = "20.11.2026"
        return dane
    if mod == "zakonczenie":
        dane.update({
            "nazwa_inwestycji": "Budowa budynku mieszkalnego jednorodzinnego",
            "adres-miejscowosc": "Myślenice", "adres-nr_dzialki": "1358",
            "zak-data_sporzadzenia": "20.11.2026",
            "zak-miejscowosc_sporzadzenia": "Nowy Targ",
            "zak-pozwolenie_znak": "AB.123.2025",
            "zak-zgodnosc": "zgodnie",
            "zak-kubatura_mieszkalna": "420",
            "zak-rodzaje_obiektu": ["nowy", "mieszkalny"],
            "zak-zalaczniki": ["dziennik_budowy"],
        })
        return dane
    if mod == "test_formularz_p":
        dane.update({
            "p-wnioskodawca": "Anna Testowa\nul. Przykładowa 12/2, 34-400 Nowy Targ",
            "p-data": "20.11.2026", "p-telefon": "600 123 456",
            "p-kontakt": "anna@example.invalid", "p-oznaczenie": "TEST/P/2026/01",
            "p-material": ["mapa", "egib"], "p-materialy_opis": "Mapa zasadnicza, skala 1:500",
            "p-cel": "wlasne", "p-teren": "małopolskie, nowotarski, Nowy Targ, ul. Testowa 25",
            "p-dzialki": "1401/2", "p-obreb": "Nowy Targ", "p-kontakt_osoba": "Anna Testowa",
            "p-email": "anna@example.invalid", "p-sposob": ["osobiscie"],
        })
        return dane
    module = importlib.import_module(mod)
    specific = copy.deepcopy(module.BASE)
    specific.update(COMMON)
    specific["dokumenty"] = kod
    specific["wybor_potwierdzony"] = "tak"
    return specific


def zapisz_wynik(response, folder: Path, nazwa: str):
    if response.status_code != 200:
        raise RuntimeError(f"Nie udało się wygenerować {nazwa}: HTTP {response.status_code}: {response.get_data(as_text=True)}")
    with zipfile.ZipFile(io.BytesIO(response.data)) as arch:
        pliki = [(n, arch.read(n)) for n in arch.namelist() if n.lower().endswith(".docx")]
    if not pliki:
        raise RuntimeError(f"Wynik {nazwa} nie zawiera DOCX.")
    if len(pliki) == 1:
        (folder / nazwa).write_bytes(pliki[0][1])
    else:
        for nr, (_, zawartosc) in enumerate(pliki, 1):
            (folder / nazwa.replace(".docx", f"_{nr}.docx")).write_bytes(zawartosc)


def main():
    katalog = ROOT / "manual_tests"
    fixture = ROOT / "tests" / "fixtures" / "obiegowka_testowa_pelna.docx"
    indeks = []
    for folder_name, (kod, mod, brak_pole, brak_wartosc, opis_braku) in TEST_CASES.items():
        folder = katalog / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "01_obiegowka_testowa.docx").write_bytes(fixture.read_bytes())
        form = baza(kod, mod)
        with app.test_client() as klient:
            poprawny = klient.post("/generuj", data=form)
            zapisz_wynik(poprawny, folder, "02_wynik_poprawny.docx")
            zmieniony = copy.deepcopy(form)
            zmieniony[brak_pole] = brak_wartosc
            bledny = klient.post("/generuj", data=zmieniony)
        if bledny.status_code == 200:
            zapisz_wynik(bledny, folder, "03_wynik_z_brakiem.docx")
            wynik = {"http": 200, "interpretacja": "Program pozwala wygenerować dokument z pustym polem; sprawdź oznaczenie pustego miejsca."}
        else:
            wynik = {"http": bledny.status_code, "komunikat": bledny.get_data(as_text=True)}
        scenariusz = {
            "dokument": kod,
            "scenariusz": opis_braku,
            "pole_do_usuniecia_lub_wyczyszczenia": brak_pole,
            "wartosc_w_przypadku_poprawnym": form.get(brak_pole),
            "wartosc_w_przypadku_brakujacym": brak_wartosc,
            "oczekiwany_wynik": wynik,
            "dane_poprawnego_przebiegu": form,
            "instrukcja": "Wgraj 01_obiegowka_testowa.docx, wybierz wskazany dokument, przepisz dane z dane_poprawnego_przebiegu; dla próby błędnej wyczyść pole wskazane wyżej.",
        }
        (folder / "03_scenariusz_brakujacy.json").write_text(json.dumps(scenariusz, ensure_ascii=False, indent=2), encoding="utf-8")
        opis = (
            f"{RODZAJE[folder_name]}\n\n"
            "01_obiegowka_testowa.docx — fikcyjne dane źródłowe do wgrania w aplikacji.\n"
            "02_wynik_poprawny.docx — przykładowy, wygenerowany poprawny dokument.\n"
            "03_scenariusz_brakujacy.json — komplet danych do powtórzenia poprawnego przebiegu oraz jedno pole do wyczyszczenia.\n"
        )
        if bledny.status_code == 200:
            opis += "03_wynik_z_brakiem.docx — przykład wyniku, gdy aplikacja dopuszcza puste pole do późniejszego ręcznego uzupełnienia.\n"
        else:
            opis += f"Oczekiwany wynik próby z brakiem: HTTP {bledny.status_code} — {bledny.get_data(as_text=True)}\n"
        opis += "Dane są fikcyjne. Podpisy złóż po wydrukowaniu; nie składaj tych przykładów do urzędu.\n"
        (folder / "JAK_TESTOWAC.txt").write_text(opis, encoding="utf-8")
        indeks.append({"folder": folder_name, "kod": kod, "poprawny_http": poprawny.status_code,
                       "brakujacy_http": bledny.status_code, "blad": bledny.get_data(as_text=True) if bledny.status_code != 200 else None})
        print(f"{folder_name}: poprawny={poprawny.status_code}, brakujący={bledny.status_code}")
    katalog.mkdir(parents=True, exist_ok=True)
    (katalog / "WYNIKI_GENEROWANIA.json").write_text(json.dumps(indeks, ensure_ascii=False, indent=2), encoding="utf-8")
    (katalog / "README.md").write_text(
        "# Ręczne testy 15 dokumentów\n\n"
        "Każdy folder ma plik obiegówki testowej, przykład poprawnego wyniku i scenariusz z brakującym polem. "
        "Dane są fikcyjne. Najpierw wgraj obiegówkę i wybierz jeden typ dokumentu; szczegółowe wartości i brakujące pole są w pliku JSON.\n\n"
        "Jeśli scenariusz kończy się HTTP 400, sprawdź komunikat walidacji. Jeśli aplikacja generuje dokument, porównaj go z `03_wynik_z_brakiem.docx` i sprawdź, czy puste pole jest widoczne.\n\n"
        "W każdym przebiegu wybierz pojedynczy typ dokumentu zgodny z nazwą folderu. Nie używaj tych danych do wniosków urzędowych.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
