"""Formularz P — wniosek o udostępnienie materiałów PZGiK (Dz.U. 2026 poz. 1068)."""
from __future__ import annotations

import datetime
import re
import io
from docx import Document

MATERIALY = {
    "mapa": "Mapa zasadnicza lub mapa ewidencji gruntów i budynków",
    "egib": "Baza danych ewidencji gruntów i budynków (EGiB)",
    "gesut": "Baza danych geodezyjnej ewidencji sieci uzbrojenia terenu (GESUT)",
    "bdot500": "Baza danych obiektów topograficznych BDOT500",
    "raporty": "Raporty tworzone na podstawie bazy danych EGiB",
    "inne": "Inne materiały",
}
CELE = {
    "wlasne": "Potrzeby własne niezwiązane z działalnością gospodarczą; bez prawa publikacji w Internecie",
    "publiczne": "Wykonanie zadań publicznych",
    "dowolne": "Dowolne potrzeby",
    "operator": "Kolejne udostępnienie danych o sieci uzbrojenia terenu podmiotowi władającemu siecią",
    "edukacja": "Cele edukacyjne (jednostka oświatowa, uczelnia lub podmiot pożytku publicznego)",
    "nauka": "Prowadzenie badań naukowych lub prac rozwojowych",
    "bezpieczenstwo": "Ustawowe zadania służb specjalnych w zakresie ochrony bezpieczeństwa państwa",
    "obronnosc": "Zadania w zakresie obronności państwa — Minister Obrony Narodowej",
    "operator_pierwszy": "Pierwsze udostępnienie danych o sieci podmiotowi władającemu siecią",
}
CL = {"wlasne": "1.0", "publiczne": "1.0", "dowolne": "2.0", "operator": "0.1"}
SPOSOBY = {
    "osobiscie": "Odbiór osobisty w siedzibie organu",
    "adres_naglowek": "Wysyłka na adres wskazany w nagłówku",
    "adres_inny": "Wysyłka na inny adres",
    "ftp": "Usługa sieciowa — serwer FTP",
    "email": "Usługa sieciowa — na wskazany adres e-mail",
    "nosnik": "Na nośniku dostarczonym przez wnioskodawcę",
}
NUMER = re.compile(r"\d+(?:/\d+)?(?:,\s*\d+(?:/\d+)?)*")


def domyslne(dane, dzisiaj):
    osoby = dane.get("inwestorzy", [])
    pierwszy = osoby[0] if osoby else {}
    adresy = []
    for osoba in osoby:
        ulica = " ".join(x for x in (osoba.get("ulica", ""), osoba.get("nr_domu", "")) if x)
        if osoba.get("nr_lokalu"):
            ulica += "/" + osoba["nr_lokalu"]
        miejscowosc = " ".join(x for x in (osoba.get("kod_pocztowy", ""), osoba.get("miejscowosc", "")) if x)
        adresy.append(" ".join(x for x in (ulica, miejscowosc) if x))
    wnioskodawca = "\n".join(x for x in [", ".join(i.get("imie_nazwisko", "") for i in osoby), "; ".join(dict.fromkeys(adresy))] if x)
    adr = dane.get("adres_inwestycji", {})
    nier = dane.get("nieruchomosc", {})
    teren = " ".join(x for x in (
        nier.get("wojewodztwo", ""), nier.get("powiat", ""), nier.get("gmina", ""),
        adr.get("miejscowosc", ""), adr.get("ulica", ""), adr.get("nr_domu", ""),
        ("dz. " + adr.get("nr_dzialki", "")) if adr.get("nr_dzialki") else "",
    ) if x)
    return {
        "wnioskodawca": wnioskodawca, "data": dzisiaj,
        "kontakt": "", "oznaczenie": "", "materialy_opis": "",
        "teren": teren, "dzialki": adr.get("nr_dzialki", ""), "obreb": adr.get("miejscowosc", ""),
        "kontakt_osoba": pierwszy.get("imie_nazwisko", ""),
        "email": pierwszy.get("email", ""), "telefon": "", "adres_inny": "",
        "ftp": "", "nosnik": "", "uwagi": "",
    }


def odczytaj(form, dane):
    limity = {"wnioskodawca": 700, "data": 10, "kontakt": 254, "oznaczenie": 100,
              "materialy_opis": 1000, "teren": 500, "dzialki": 500, "obreb": 200,
              "kontakt_osoba": 200, "email": 254, "telefon": 40, "adres_inny": 500,
              "ftp": 254, "nosnik": 200, "uwagi": 1200}
    wynik = {}
    for pole, limit in limity.items():
        wartosci = form.getlist("p-" + pole)
        wartosc = form.get("p-" + pole, "").strip()
        if len(wartosci) > 1 or len(wartosc) > limit or any(ord(c) < 32 and c not in "\r\n\t" for c in wartosc):
            raise ValueError("Formularz P: sprawdź długość lub zawartość pól.")
        wynik[pole] = wartosc
    wynik["materialy"] = _wybory(form, "material", MATERIALY)
    wynik["cele"] = _wybory(form, "cel", CELE)
    wynik["sposoby"] = _wybory(form, "sposob", SPOSOBY)
    if not wynik["wnioskodawca"]:
        raise ValueError("Formularz P: podaj wnioskodawcę i adres.")
    if not wynik["materialy"]:
        raise ValueError("Formularz P: zaznacz co najmniej jeden rodzaj materiału.")
    if len(wynik["cele"]) != 1:
        raise ValueError("Formularz P: wybierz jeden cel udostępnienia materiałów.")
    if not wynik["sposoby"]:
        raise ValueError("Formularz P: wybierz sposób udostępnienia materiałów.")
    if not wynik["teren"] and not wynik["dzialki"]:
        raise ValueError("Formularz P: podaj lokalizację materiałów lub numery działek.")
    if wynik["dzialki"] and not NUMER.fullmatch(wynik["dzialki"]):
        raise ValueError("Formularz P: sprawdź numery działek, np. 123/4, 125.")
    try:
        dt = datetime.datetime.strptime(wynik["data"], "%d.%m.%Y").date()
        if dt.strftime("%d.%m.%Y") != wynik["data"]: raise ValueError()
    except ValueError:
        raise ValueError("Formularz P: podaj prawidłową datę w formacie DD.MM.RRRR.")
    if wynik["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", wynik["email"]):
        raise ValueError("Formularz P: podaj prawidłowy adres e-mail.")
    if wynik["telefon"] and (not re.fullmatch(r"[+\d\s()\-]+", wynik["telefon"]) or not 7 <= len(re.sub(r"\D", "", wynik["telefon"])) <= 15):
        raise ValueError("Formularz P: sprawdź numer telefonu.")
    if "adres_inny" in wynik["sposoby"] and not wynik["adres_inny"]:
        raise ValueError("Formularz P: podaj adres wysyłki.")
    if "email" in wynik["sposoby"] and not wynik["email"]:
        raise ValueError("Formularz P: podaj e-mail do udostępnienia materiałów.")
    if "ftp" in wynik["sposoby"] and not wynik["ftp"]:
        raise ValueError("Formularz P: podaj dane / adres serwera FTP.")
    return wynik


def _wybory(form, nazwa, slownik):
    wybrane = form.getlist(f"p-{nazwa}")
    if len(wybrane) != len(set(wybrane)) or any(x not in slownik for x in wybrane):
        raise ValueError("Formularz P: nieprawidłowy wybór pola.")
    return wybrane


def kontekst(dane):
    return dane["formularz_p"]


def zastosuj(docx_bytes: bytes, dane: dict) -> bytes:
    doc = Document(io.BytesIO(docx_bytes))
    wybrane = {"MATERIAL": set(dane["materialy"]), "CEL": set(dane["cele"]), "SPOSOB": set(dane["sposoby"])}
    for para in [*doc.paragraphs, *(p for t in doc.tables for r in t.rows for c in r.cells for p in c.paragraphs)]:
        for run in para.runs:
            style = run.style.name if run.style else ""
            m = re.fullmatch(r"P_(MATERIAL|CEL|SPOSOB)_(.+)", style)
            if m:
                run.text = "☒" if m.group(2).lower() in wybrane[m.group(1)] else "☐"
    out = io.BytesIO(); doc.save(out); return out.getvalue()
