"""OŚ-6165: wniosek o zaświadczenie dotyczące uproszczonego planu lasu."""
import io
import zipfile

import pytest
from docx import Document

from app.main import app

BASE = {
    "dokumenty": "os616", "wybor_potwierdzony": "tak",
    "inw-0-imie_nazwisko": "Krzysztof Testowy", "inw-0-miejscowosc": "Kraków",
    "inw-0-ulica": "ul. Przykładowa", "inw-0-nr_domu": "12", "inw-0-kod_pocztowy": "30-001",
    "adres-miejscowosc": "Nowy Targ", "adres-nr_dzialki": "245/7",
    "os616-wnioskodawca": "Krzysztof Testowy\nul. Przykładowa 12\n30-001 Kraków",
    "os616-telefon": "600 123 456", "os616-data": "19.11.2026",
    "os616-dzialki": "245/7, 246", "os616-miejscowosc": "Nowy Targ",
    "os616-odbior": "osobiscie_dzis",
}


def pobierz(form):
    with app.test_client() as c:
        response = c.post("/generuj", data=form)
    assert response.status_code == 200, response.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(response.data)) as z:
        assert z.namelist() == ["OS-6165_Zaswiadczenie_UPUL_Testowy.docx"]
        return Document(io.BytesIO(z.read(z.namelist()[0]))), z.read(z.namelist()[0])


def tekst(d):
    return "\n".join(p.text for p in d.paragraphs)


def test_os616_dane_klauzula_i_sposob_odbioru():
    d, _ = pobierz(BASE)
    t = tekst(d)
    for fragment in [
        "OŚ-6165", "Krzysztof Testowy", "600 123 456", "Nowy Targ, dnia 19.11.2026",
        "245/7, 246", "art. 19 ust. 3 ustawy o lasach", "17 zł",
        "20 1240 6292 1111 0011 2118 2790", "Starostwo Powiatowe w Nowym Targu",
        "https://www.nowotarski.pl/polityka-prywatnosci/dokumenty/polityka-prywatnosci-812.html",
    ]:
        assert fragment in t
    assert "{{" not in t
    odbiory = {r.style.name: r.text for p in d.paragraphs for r in p.runs if r.style.name.startswith("OS616_ODBIOR_")}
    assert odbiory == {
        "OS616_ODBIOR_OSOBISCIE_DZIS": "☒",
        "OS616_ODBIOR_OSOBISCIE_INNY": "☐",
        "OS616_ODBIOR_POCZTA": "☐",
    }
    assert len([p for p in d.paragraphs if p.text == ""]) > 0


@pytest.mark.parametrize("zmiany,blad", [
    ({"os616-wnioskodawca": ""}, "podaj imię i nazwisko"),
    ({"os616-dzialki": "abc"}, "numery działek"),
    ({"os616-dzialki": "12, 12"}, "bez powtórzeń"),
    ({"os616-data": "31.02.2026"}, "prawidłową datę"),
    ({"os616-odbior": ""}, "wybierz jeden sposób odbioru"),
])
def test_os616_bledne_dane_blokuja_generowanie(zmiany, blad):
    with app.test_client() as c:
        response = c.post("/generuj", data=BASE | zmiany)
    assert response.status_code == 400
    assert blad in response.get_data(as_text=True)
