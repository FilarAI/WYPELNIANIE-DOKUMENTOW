"""Lokalny serwer (tylko 127.0.0.1): wgranie obiegówki → formularz z danymi → dokumenty
(zapis do wybranego folderu albo pobranie ZIP).

Uruchomienie: python -m app.main [--port 5050] [--bez-przegladarki]
"""
from __future__ import annotations

import argparse
import datetime
import io
import os
import re
import socket
import threading
import traceback
import webbrowser

from flask import Flask, Response, jsonify, render_template, request

from app import WERSJA, teryt, zapis
from app.generator import generuj_dokumenty, spakuj
from app.parser_obiegowki import NAZWY_POL, odczytaj_obiegowke

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
FOLDER_PROGRAMU = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@app.context_processor
def informacje_o_programie():
    # Widoczne w stopce każdej strony – pozwala sprawdzić, czy ikona uruchamia aktualną wersję.
    return {"wersja": WERSJA, "folder_programu": FOLDER_PROGRAMU}

POLA_INWESTORA = ["imie_nazwisko", "plec", "ulica", "nr_domu", "nr_lokalu", "kod_pocztowy", "miejscowosc",
                  "poczta", "wojewodztwo", "powiat", "gmina"]
POLA_ADRESU = ["miejscowosc", "ulica", "nr_domu", "kod_pocztowy", "nr_dzialki", "identyfikator_dzialki"]
POLA_JEDNOSTKI = ["wojewodztwo", "powiat", "gmina"]


@app.get("/")
def start():
    return render_template("start.html")


@app.post("/podglad")
def podglad():
    plik = request.files.get("obiegowka")
    if not plik or not plik.filename:
        return render_template("start.html", blad="Nie wybrano pliku.")
    if not plik.filename.lower().endswith(".docx"):
        return render_template("start.html", blad="Obsługiwane są tylko pliki Word .docx. "
                                                  "Plik .doc otwórz w Wordzie i zapisz jako .docx.")
    try:
        # Wczytanie do pamięci: strumień uploadu na Pythonie 3.9 nie obsługuje seekable(), a docx to ZIP.
        dane = odczytaj_obiegowke(io.BytesIO(plik.read()))
    except ValueError as e:
        return render_template("start.html", blad=str(e))
    except Exception:
        traceback.print_exc()
        return render_template("start.html", blad="Nie udało się odczytać pliku. Czy to na pewno dokument Word (.docx)?")
    if not dane["inwestorzy"]:
        dane["inwestorzy"] = [{k: "" for k in POLA_INWESTORA} | {"plec": "M"}]
    pola_z_ostrzezeniem = {o["pole"] for o in dane["ostrzezenia"]}
    return render_template("podglad.html", dane=dane, nazwa_pliku=plik.filename,
                           pola_z_ostrzezeniem=pola_z_ostrzezeniem, nazwy_pol=NAZWY_POL,
                           dzisiaj=datetime.date.today().strftime("%d.%m.%Y"),
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
    return {
        "nazwa_inwestycji": " ".join(f.get("nazwa_inwestycji", "").split()),
        "adres_inwestycji": adres,
        "nieruchomosc": nieruchomosc,
        "inwestorzy": inwestorzy,
        "data_pelnomocnictwa": f.get("data_pelnomocnictwa", "").strip(),
        "upowazniony_w_pb5": f.get("upowazniony_w_pb5") == "tak",
    }


@app.post("/generuj")
def generuj():
    dane = _dane_z_formularza(request.form)
    if not dane["inwestorzy"]:
        return Response("Podaj co najmniej jednego inwestora (imię i nazwisko). Wróć do formularza.", status=400,
                        mimetype="text/plain; charset=utf-8")
    pliki = generuj_dokumenty(dane)

    if request.form.get("akcja") == "zapisz":
        try:
            folder = zapis.sprawdz_folder(request.form.get("folder_zapisu", ""))
            zapisane = zapis.zapisz_pliki(folder, pliki)
        except ValueError as e:
            return render_template("zapisano.html", blad=str(e)), 400
        except OSError as e:
            return render_template("zapisano.html", blad=f"Nie udało się zapisać plików: {e.strerror}."), 500
        zapis.zapamietaj_folder(str(folder))
        return render_template("zapisano.html", folder=folder, zapisane=[p.name for p in zapisane])

    nazwa_zip = next(iter(pliki)).replace("Pelnomocnictwo_", "Dokumenty_").replace(".docx", ".zip")
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
    return render_template("koniec.html")


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
