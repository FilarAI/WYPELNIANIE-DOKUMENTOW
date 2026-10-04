import json
import subprocess
from pathlib import Path

import pytest

from app import zapis
from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"
FORMULARZ = {
    "nazwa_inwestycji": "BUDOWA DOMU",
    "adres-identyfikator_dzialki": "121701_1.0005.245/7", "adres-nr_dzialki": "245/7",
    "adres-miejscowosc": "Zakopane", "adres-ulica": "ul. Słoneczna", "adres-nr_domu": "8",
    "inw-0-imie_nazwisko": "Krzysztof Testowy", "inw-0-plec": "M", "inw-0-miejscowosc": "Kraków",
    "data_pelnomocnictwa": "04.10.2026",
}


@pytest.fixture(autouse=True)
def ustawienia(tmp_path, monkeypatch):
    plik = tmp_path / "ustawienia.json"
    monkeypatch.setenv("DOKUMENTY_FILAR_USTAWIENIA", str(plik))
    return plik


@pytest.fixture
def klient():
    app.config["TESTING"] = True
    return app.test_client()


def test_zapis_do_folderu_i_zapamietanie(klient, tmp_path, ustawienia):
    folder = tmp_path / "Klienci"
    folder.mkdir()
    odp = klient.post("/generuj", data=FORMULARZ | {"akcja": "zapisz", "folder_zapisu": str(folder)})
    assert odp.status_code == 200
    assert sorted(p.name for p in folder.iterdir()) == ["PB-5_Testowy_Krzysztof.docx", "Pelnomocnictwo_Testowy.docx"]
    assert "Gotowe" in odp.get_data(as_text=True)
    assert json.loads(ustawienia.read_text(encoding="utf-8"))["folder_zapisu"] == str(folder)
    assert zapis.ostatni_folder() == str(folder)


def test_zapis_nie_nadpisuje_istniejacych(klient, tmp_path):
    for _ in range(2):
        klient.post("/generuj", data=FORMULARZ | {"akcja": "zapisz", "folder_zapisu": str(tmp_path)})
    nazwy = {p.name for p in tmp_path.iterdir()}
    assert {"Pelnomocnictwo_Testowy.docx", "Pelnomocnictwo_Testowy (2).docx"} <= nazwy


def test_zapis_do_nieistniejacego_folderu(klient, tmp_path):
    odp = klient.post("/generuj", data=FORMULARZ | {"akcja": "zapisz", "folder_zapisu": str(tmp_path / "brak")})
    assert odp.status_code == 400
    assert "nie istnieje" in odp.get_data(as_text=True)


def test_formularz_podpowiada_ostatni_folder(klient, tmp_path):
    zapis.zapamietaj_folder(str(tmp_path))
    with open(FIXTURES / "obiegowka_przyklad.docx", "rb") as f:
        html = klient.post("/podglad", data={"obiegowka": (f, "o.docx")},
                           content_type="multipart/form-data").get_data(as_text=True)
    assert f'value="{tmp_path}"' in html


def test_okno_wyboru_folderu(klient, monkeypatch, tmp_path):
    monkeypatch.setattr(zapis.sys, "platform", "darwin")
    wywolania = []

    def udawany_osascript(polecenie, **_):
        wywolania.append(polecenie)
        return subprocess.CompletedProcess(polecenie, 0, stdout=f"{tmp_path}/\n", stderr="")

    monkeypatch.setattr(zapis.subprocess, "run", udawany_osascript)
    odp = klient.post("/wybierz-folder", data={"obecny": str(tmp_path)}).get_json()
    assert odp == {"folder": str(tmp_path)}
    assert wywolania[0][0] == "osascript" and "choose folder" in wywolania[0][2]


def test_okno_wyboru_folderu_anulowane(klient, monkeypatch):
    monkeypatch.setattr(zapis.sys, "platform", "darwin")
    monkeypatch.setattr(zapis.subprocess, "run",
                        lambda p, **_: subprocess.CompletedProcess(p, 1, stdout="", stderr="User canceled. (-128)"))
    assert klient.post("/wybierz-folder").get_json() == {"anulowano": True}


def test_okno_wyboru_folderu_poza_macos(klient, monkeypatch):
    monkeypatch.setattr(zapis.sys, "platform", "linux")
    assert "tylko na macOS" in klient.post("/wybierz-folder").get_json()["blad"]
