"""Lokalny serwer (tylko 127.0.0.1): wgranie źródeł → formularz z danymi → dokumenty
(zapis do wybranego folderu albo pobranie ZIP).

Uruchomienie: python -m app.main [--port 5050] [--bez-przegladarki]
"""
from __future__ import annotations

import argparse
import base64
import datetime
import os
import re
import secrets
import socket
import threading
import time
import webbrowser

from flask import Flask, Response, jsonify, render_template, request

from app.prezentacja import klucz_nazwy, ostrzezenie_ui
from app import WERSJA, dokumenty, dziennik, ewidencja, egib_wypis, formularz_p, formatowanie, os616, pb1, pb2, pb2a, pb7, pb9, teryt, zapis, zakonczenie
from app.generator import generuj_dokumenty, spakuj
from app.parser_obiegowki import NAZWY_POL
from app.parser_zrodel import RODZAJE_ZRODEL
from app.scalanie_zrodel import odczytaj_zestaw
from app.konfiguracja import PELNOMOCNIK

app = Flask(__name__)
app.add_template_filter(ostrzezenie_ui, "ostrzezenie_ui")
app.config["MAX_CONTENT_LENGTH"] = 150 * 1024 * 1024
FOLDER_PROGRAMU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_wgrane: dict[str, tuple[float, dict, str]] = {}
_blokada_wgranych = threading.Lock()
_szkice: dict[str, list] = {}


@app.after_request
def naglowki_prywatnosci(odpowiedz):
    odpowiedz.headers["X-Content-Type-Options"] = "nosniff"
    odpowiedz.headers["X-Frame-Options"] = "DENY"
    odpowiedz.headers["Referrer-Policy"] = "no-referrer"
    if not request.path.startswith("/static/"):
        odpowiedz.headers["Cache-Control"] = "no-store"
    return odpowiedz


@app.context_processor
def informacje_o_programie():
    # Widoczne w stopce każdej strony – pozwala sprawdzić, czy ikona uruchamia aktualną wersję.
    return {"wersja": WERSJA, "folder_programu": FOLDER_PROGRAMU, "wersja_stylu": _wersja_stylu()}


def _wersja_stylu() -> int:
    # Czas zmiany plików wyglądu w adresie: po aktualizacji programu przeglądarka pobiera nowy wygląd.
    try:
        return int(max(os.path.getmtime(os.path.join(app.static_folder, n)) for n in ("styl.css", "ui-v2.css", "ui-v2.js")))
    except OSError:
        return 0

POLA_INWESTORA = ["imie_nazwisko", "plec", "ulica", "nr_domu", "nr_lokalu", "kod_pocztowy", "miejscowosc",
                  "poczta", "wojewodztwo", "powiat", "gmina"]
POLA_ADRESU = ["miejscowosc", "ulica", "nr_domu", "kod_pocztowy", "nr_dzialki", "identyfikator_dzialki"]
POLA_JEDNOSTKI = ["wojewodztwo", "powiat", "gmina"]


@app.get("/")
def start():
    return render_template("start.html", rodzaje_zrodel=RODZAJE_ZRODEL)


def _odczytaj_plik():
    pliki = []
    for nr, klucz in enumerate(("obiegowka", "plik_1", "plik_2")):
        plik = request.files.get(klucz)
        if plik and plik.filename:
            nazwa = os.path.basename(plik.filename)[:180]
            typ = request.form.get(f"typ_{nr}", "obiegowka" if nr == 0 else "")
            pliki.append((typ, nazwa, plik.read()))
    if not pliki:
        raise ValueError("Nie wybrano pliku.")
    try:
        dane = odczytaj_zestaw(pliki)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Nie udało się odczytać pliku. Sprawdź jego format i wybrany typ.")
    if not dane["inwestorzy"]:
        dane["inwestorzy"] = [{k: "" for k in POLA_INWESTORA} | {"plec": "M"}]
    return dane, ", ".join(nazwa for _, nazwa, _ in pliki)


@app.post("/sprawdz-plik")
def sprawdz_plik():
    from app.kontrola_pliku import sprawdz
    plik = request.files.get("plik")
    if not plik or not plik.filename:
        return jsonify(blad="Wybierz plik Word lub PDF."), 400
    try:
        return jsonify(sprawdz(plik.read(), os.path.basename(plik.filename)))
    except ValueError as e:
        return jsonify(blad=str(e)), 400
    except Exception:
        return jsonify(blad="Nie udało się odczytać pliku. Sprawdź, czy dokument nie jest uszkodzony lub zabezpieczony hasłem."), 400


@app.post("/wybierz-dokumenty")
def wybierz_dokumenty():
    try:
        dane, nazwa = _odczytaj_plik()
    except ValueError as e:
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify(blad=str(e)), 400
        return render_template("start.html", blad=str(e), rodzaje_zrodel=RODZAJE_ZRODEL), 400
    token = secrets.token_urlsafe(24)
    with _blokada_wgranych:
        teraz = time.monotonic()
        for stary, (czas, _, _) in list(_wgrane.items()):
            if teraz - czas > 3600:
                del _wgrane[stary]
                _szkice.pop(stary, None)
        if len(_wgrane) >= 100:
            najstarszy = min(_wgrane, key=lambda x: _wgrane[x][0])
            del _wgrane[najstarszy]
            _szkice.pop(najstarszy, None)
        _wgrane[token] = (teraz, dane, nazwa)
    if request.headers.get("X-Requested-With") == "fetch":
        return jsonify(token=token)
    return render_template("wybor_dokumentow.html", token=token, nazwa_pliku=nazwa,
                           dokumenty=dict(sorted(dokumenty.DOKUMENTY.items(), key=lambda x: klucz_nazwy(x[1]))), domyslne=dokumenty.DOMYSLNE,
                           pliki_zrodlowe=dane["pliki_zrodlowe"])


@app.get("/wybierz-dokumenty")
def powrot_do_wyboru():
    token = request.args.get("token", "")
    with _blokada_wgranych:
        wpis = _wgrane.get(token)
    if not wpis or time.monotonic() - wpis[0] > 3600:
        return render_template("start.html", blad="Wygasły pliki. Wgraj je ponownie.", rodzaje_zrodel=RODZAJE_ZRODEL), 400
    return render_template("wybor_dokumentow.html", token=token, nazwa_pliku=wpis[2],
                           dokumenty=dict(sorted(dokumenty.DOKUMENTY.items(), key=lambda x: klucz_nazwy(x[1]))),
                           domyslne=request.args.getlist("dokumenty") or dokumenty.DOMYSLNE,
                           pliki_zrodlowe=wpis[1]["pliki_zrodlowe"])


@app.post("/sprawdz-dane")
def sprawdz_dane():
    token = request.form.get("token_wgrania", "")
    with _blokada_wgranych:
        wpis = _wgrane.get(token)
        if not wpis or time.monotonic() - wpis[0] > 3600:
            return jsonify(zadania=[{"kod": "", "opis": "Wygasły pliki źródłowe. Wgraj je ponownie."}], wygaslo=True), 400
        _szkice[token] = list(request.form.items(multi=True))
    zadania = []
    try:
        wybrane = dokumenty.odczytaj_wybor(request.form)
    except ValueError as e:
        return jsonify(zadania=[{"kod": "", "opis": str(e)}]), 400
    if wpis[1].get("blokada_zestawu"):
        zadania.append({"kod": "", "opis": "Pliki dotyczą różnych inwestycji. Zmień pliki źródłowe."})
    for kod in wybrane:
        formularz = request.form.copy()
        formularz.setlist("dokumenty", [kod])
        try:
            dane = _dane_z_formularza(formularz)
            if not dane["inwestorzy"]:
                raise ValueError("Podaj co najmniej jednego inwestora (imię i nazwisko).")
        except ValueError as e:
            zadania.append({"kod": kod, "opis": str(e)})
    return jsonify(zadania=zadania)


@app.post("/podglad")
def podglad():
    token = request.form.get("token")
    if token:
        with _blokada_wgranych:
            wgrane = _wgrane.get(token)
        if not wgrane or time.monotonic() - wgrane[0] > 3600:
            return render_template("start.html", blad="Wygasły wgrane pliki. Wgraj je ponownie.",
                                   rodzaje_zrodel=RODZAJE_ZRODEL), 400
        _, dane, nazwa = wgrane
        try:
            wybrane = dokumenty.odczytaj_wybor(request.form)
        except ValueError as e:
            return Response(str(e), status=400, mimetype="text/plain; charset=utf-8")
    else:
        # Zgodność ze starszymi formularzami i testami wysyłającymi plik wprost do /podglad.
        try:
            dane, nazwa = _odczytaj_plik()
        except ValueError as e:
            return render_template("start.html", blad=str(e), rodzaje_zrodel=RODZAJE_ZRODEL), 400
        wybrane = dokumenty.DOMYSLNE
    pola_z_ostrzezeniem = {o["pole"] for o in dane["ostrzezenia"]}
    return render_template("podglad.html", dane=dane, nazwa_pliku=nazwa,
                           szkic=_szkice.get(token, []), wybrane=wybrane, nazwy_dokumentow=dokumenty.DOKUMENTY,
                           pola_z_ostrzezeniem=pola_z_ostrzezeniem, nazwy_pol=NAZWY_POL,
                           dzisiaj=datetime.date.today().strftime("%d.%m.%Y"),
                           zak={"miejscowosc_sporzadzenia": dane["adres_inwestycji"].get("miejscowosc", ""),
                                "data_sporzadzenia": datetime.date.today().strftime("%d.%m.%Y"),
                                **dane.get("zakonczenie", {})},
                           token_wgrania=token or "", pliki_zrodlowe=dane.get("pliki_zrodlowe", []),
                           pochodzenie=dane.get("pochodzenie", []), konflikty=dane.get("konflikty", []),
                           potwierdzenia=dane.get("potwierdzenia", []),
                           blokada_zestawu=dane.get("blokada_zestawu", False),
                           dzialki_do_wyboru=dane.get("dzialki_do_wyboru", []),
                           limity_zak=zakonczenie.POLA_TEKSTOWE,
                           wybory_zak=zakonczenie.WYBORY,
                           rodzaje_obiektu=zakonczenie.RODZAJE_OBIEKTU,
                           zalaczniki=zakonczenie.ZALACZNIKI,
                           kierownik=PELNOMOCNIK,
                           kierownik_adres=zakonczenie.adres_kierownika(),
                           pb2_pola=pb2.POLA,
                           pb2_adres=pb2.ADRES,
                           pb2a_rodzaje=pb2a.RODZAJE,
                           pb1_rodzaje=pb1.RODZAJE,
                           os616_wartosci=os616.domyslne(dane, datetime.date.today().strftime("%d.%m.%Y")),
                           egibw_wartosci=egib_wypis.domyslne(dane, datetime.date.today().strftime("%d.%m.%Y")),
                           egibw_przedmioty=egib_wypis.PRZEDMIOTY, egibw_uzasadnienia=egib_wypis.UZASADNIENIA,
                           egibw_postac=egib_wypis.POSTAC, egibw_odbior=egib_wypis.ODBIOR,
                           p_wartosci=formularz_p.domyslne(dane, datetime.date.today().strftime("%d.%m.%Y")),
                           p_materialy=formularz_p.MATERIALY, p_cele=formularz_p.CELE,
                           p_sposoby=formularz_p.SPOSOBY,
                           ba4_wartosci=dziennik.domyslne(dane, datetime.date.today().strftime("%d.%m.%Y")),
                           ba4_wybory=dziennik.WYBORY, ba4_etykiety=dziennik.ETYKIETY, ba4_pola=dziennik.POLA,
                           egib_wartosci=ewidencja.domyslne(dane, datetime.date.today().strftime("%d.%m.%Y")),
                           egib_pola=ewidencja.POLA, egib_role=ewidencja.ROLE,
                           pelnomocnicy=dane.get("inwestorzy", []),
                           folder_zapisu=zapis.ostatni_folder())


def _dane_z_formularza(f) -> dict:
    indeksy = sorted({int(m.group(1)) for k in f if (m := re.match(r"inw-(\d+)-", k))})
    inwestorzy = []
    for i in indeksy:
        inw = {p: f.get(f"inw-{i}-{p}", "").strip() for p in POLA_INWESTORA}
        if not inw["imie_nazwisko"]:
            continue
        if not inw["gmina"] and inw["miejscowosc"]:
            inw.update({k: v for k, v in vars(teryt.z_miejscowosci(inw["miejscowosc"]) or teryt.Jednostka()).items()
                        if not inw[k]})
        inwestorzy.append(inw)

    adres = {p: f.get(f"adres-{p}", "").strip() for p in POLA_ADRESU}
    nieruchomosc = {p: f.get(f"nier-{p}", "").strip() for p in POLA_JEDNOSTKI}
    if not any(nieruchomosc.values()):
        nieruchomosc = vars(teryt.z_identyfikatora(adres["identyfikator_dzialki"]) or teryt.Jednostka())
    dane = {
        "nazwa_inwestycji": " ".join(f.get("nazwa_inwestycji", "").split()),
        "adres_inwestycji": adres,
        "nieruchomosc": nieruchomosc,
        "inwestorzy": inwestorzy,
        "data_pelnomocnictwa": f.get("data_pelnomocnictwa", "").strip(),
        "upowazniony_w_pb5": f.get("upowazniony_w_pb5") == "tak",
        "dokumenty": dokumenty.odczytaj_wybor(f, domyslne=f.get("wybor_potwierdzony") != "tak"),
        "zakonczenie": zakonczenie.odczytaj_z_formularza(f),
        "formatowanie": formatowanie.odczytaj_z_formularza(f),
    }

    if "ba4" in dane["dokumenty"]:
        dane["ba4"] = dziennik.odczytaj_z_formularza(f, dane)
    if "egib" in dane["dokumenty"]:
        dane["egib"] = ewidencja.odczytaj_z_formularza(f, dane)
    if "pelnomocnictwo_egib" in dane["dokumenty"]:
        from app import pelnomocnictwo_egib
        dane["pelnomocnictwo_egib"] = pelnomocnictwo_egib.odczytaj(f, dane)
    if "pb2" in dane["dokumenty"]:
        dane["pb2"] = pb2.odczytaj(f, dane)
    if "pb2a" in dane["dokumenty"]:
        dane["pb2a"] = pb2a.odczytaj(f, dane)
    if "pb7" in dane["dokumenty"]:
        dane["pb7"] = pb7.odczytaj(f, dane)
    if "pb9" in dane["dokumenty"]:
        dane["pb9"] = pb9.odczytaj(f, dane)
    if "pb1" in dane["dokumenty"]:
        dane["pb1"] = pb1.odczytaj(f, dane)
    if "os616" in dane["dokumenty"]:
        dane["os616"] = os616.odczytaj(f, dane)
    if "egib_wypis" in dane["dokumenty"]:
        dane["egib_wypis"] = egib_wypis.odczytaj(f, dane)
    if "formularz_p" in dane["dokumenty"]:
        dane["formularz_p"] = formularz_p.odczytaj(f, dane)
    return dane


@app.post("/generuj")
def generuj():
    token = request.form.get("token_wgrania")
    if token:
        with _blokada_wgranych:
            wgrane = _wgrane.get(token)
        if not wgrane or time.monotonic() - wgrane[0] > 3600:
            return Response("Wygasły wgrane pliki. Wgraj je ponownie.", status=400)
        if wgrane[1].get("blokada_zestawu"):
            return Response("Wgrane pliki dotyczą różnych inwestycji. Usuń obcy plik.", status=400)
    try:
        dane = _dane_z_formularza(request.form)
    except ValueError as e:
        return Response(str(e), status=400, mimetype="text/plain; charset=utf-8")
    if not dane["inwestorzy"]:
        return Response("Podaj co najmniej jednego inwestora (imię i nazwisko). Wróć do formularza.", status=400,
                        mimetype="text/plain; charset=utf-8")
    pliki = generuj_dokumenty(dane)

    if request.form.get("akcja") == "zapisz":
        try:
            folder = zapis.sprawdz_folder(request.form.get("folder_zapisu", ""))
            zapisane = zapis.zapisz_pliki(folder, pliki)
        except ValueError as e:
            return (jsonify(blad=str(e)), 400) if request.headers.get("X-Requested-With") == "fetch" else (render_template("zapisano.html", blad=str(e)), 400)
        except OSError as e:
            return (jsonify(blad=f"Nie udało się zapisać plików: {e.strerror}."), 500) if request.headers.get("X-Requested-With") == "fetch" else (render_template("zapisano.html", blad=f"Nie udało się zapisać plików: {e.strerror}."), 500)
        zapis.zapamietaj_folder(str(folder))
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify(folder=str(folder), pliki=[p.name for p in zapisane])
        return render_template("zapisano.html", folder=folder, zapisane=[p.name for p in zapisane])

    pierwszy = next(iter(pliki)).rsplit(".", 1)[0]
    nazwa_zip = (("Dokumenty_" + pierwszy[len("Pelnomocnictwo_"):]) if pierwszy.startswith("Pelnomocnictwo_")
                 else "Dokumenty_" + pierwszy) + ".zip"
    return Response(spakuj(pliki), mimetype="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{nazwa_zip}"'})


@app.post("/wybierz-folder")
def wybierz_folder():
    try:
        folder = zapis.wybierz_folder_w_oknie(request.form.get("obecny", ""))
    except Exception as e:
        return jsonify(blad=str(e))
    return jsonify(folder=folder) if folder else jsonify(anulowano=True)


@app.post("/pokaz-folder")
def pokaz_folder():
    try:
        zapis.pokaz_w_finderze(zapis.sprawdz_folder(request.form.get("folder", "")))
    except ValueError as e:
        return jsonify(blad=str(e)), 400
    return jsonify(ok=True)


@app.post("/zakoncz")
def zakoncz():
    threading.Timer(0.5, lambda: os._exit(0)).start()
    # Ikona wpisana w stronę: serwer znika po pół sekundy, osobny plik mógłby się już nie wczytać.
    with open(os.path.join(app.static_folder, "ikona-192.png"), "rb") as f:
        ikona = "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
    return render_template("koniec.html", ikona_programu=ikona)


# Porty, których przeglądarki nie otwierają (ERR_UNSAFE_PORT), np. 5060/5061 – telefonia SIP.
PORTY_ZABLOKOWANE = {5060, 5061}


def _wolny_port(od: int) -> int:
    for port in range(od, od + 50):
        if port in PORTY_ZABLOKOWANE:
            continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("Brak wolnego portu")


def main():
    argumenty = argparse.ArgumentParser(description="Wypełnianie dokumentów z obiegówki – FILAR-USŁUGI")
    argumenty.add_argument("--port", type=int, default=5050)
    argumenty.add_argument("--bez-przegladarki", action="store_true")
    args = argumenty.parse_args()
    port = _wolny_port(args.port)
    adres = f"http://127.0.0.1:{port}"
    print(f"Dokumenty FILAR, wersja {WERSJA}")
    print(f"Folder programu: {FOLDER_PROGRAMU}")
    print(f"Program działa pod adresem {adres} – zamknij to okno, aby go wyłączyć.")
    if not args.bez_przegladarki:
        threading.Timer(1.0, lambda: webbrowser.open(adres)).start()
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
