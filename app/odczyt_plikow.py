"""Odczyt tekstu z DOCX i PDF, bez utrwalania dokumentów klientów."""
from __future__ import annotations

import base64
import io
import json
import os
import subprocess
import zipfile
from pathlib import Path

import fitz
from docx import Document

MAX_PLIK = 50 * 1024 * 1024
MAX_STRON = 120
MAX_ROZPAKOWANE = 180 * 1024 * 1024
OCR_SWIFT = Path(__file__).resolve().parent.parent / "narzedzia" / "ocr_vision.swift"


def _docx_linie(zawartosc: bytes) -> list[tuple[int, str]]:
    if not zipfile.is_zipfile(io.BytesIO(zawartosc)):
        raise ValueError("Plik DOCX nie jest poprawnym dokumentem Word.")
    with zipfile.ZipFile(io.BytesIO(zawartosc)) as archiwum:
        wpisy = archiwum.infolist()
        if len(wpisy) > 5000 or sum(x.file_size for x in wpisy) > MAX_ROZPAKOWANE:
            raise ValueError("Plik Word jest zbyt duży po rozpakowaniu.")
        if "word/document.xml" not in archiwum.namelist():
            raise ValueError("Plik DOCX nie zawiera treści dokumentu.")
    dokument = Document(io.BytesIO(zawartosc))
    linie = []
    for blok in dokument.iter_inner_content():
        if hasattr(blok, "rows"):
            for wiersz in blok.rows:
                komorki = [" ".join(k.text.split()) for k in wiersz.cells]
                if any(komorki):
                    linie.append((0, " | ".join(komorki)))
        else:
            tekst = " ".join(blok.text.split())
            if tekst:
                linie.append((0, tekst))
    for sekcja in dokument.sections:
        for czesc in (sekcja.header, sekcja.footer):
            for akapit in czesc.paragraphs:
                tekst = " ".join(akapit.text.split())
                if tekst:
                    linie.append((0, tekst))
    return linie


def _ocr_strony(strony: list[tuple[int, bytes]]) -> dict[int, str]:
    if not Path("/usr/bin/swift").exists():
        raise ValueError("Ten Mac nie ma narzędzia Swift potrzebnego do odczytu skanowanego PDF.")
    wejscie = "".join(json.dumps({"page": nr, "png": base64.b64encode(png).decode("ascii")}) + "\n"
                      for nr, png in strony)
    srodowisko = os.environ.copy()
    # Kompilator Swift może używać cache; trzymamy go wewnątrz lokalnego środowiska projektu.
    cache = Path(__file__).resolve().parent.parent / ".venv" / "swift-cache"
    cache.mkdir(parents=True, exist_ok=True)
    srodowisko["SWIFT_MODULECACHE_PATH"] = str(cache)
    try:
        wynik = subprocess.run(["/usr/bin/swift", "-module-cache-path", str(cache), str(OCR_SWIFT)], input=wejscie, text=True,
                               capture_output=True, timeout=180, env=srodowisko, check=False)
    except subprocess.TimeoutExpired:
        raise ValueError("Odczyt skanu PDF trwał zbyt długo.")
    if wynik.returncode:
        raise ValueError("Nie udało się uruchomić OCR skanowanego PDF na tym Macu.")
    odpowiedzi = [json.loads(l) for l in wynik.stdout.splitlines() if l.strip()]
    odczytane = {x.get("page"): x.get("text", "") for x in odpowiedzi}
    return odczytane


def _pdf_linie(zawartosc: bytes) -> tuple[list[tuple[int, str]], bool]:
    if not zawartosc.startswith(b"%PDF-"):
        raise ValueError("Plik PDF ma niepoprawną zawartość.")
    try:
        dokument = fitz.open(stream=zawartosc, filetype="pdf")
    except Exception:
        raise ValueError("Nie udało się otworzyć pliku PDF.")
    try:
        if dokument.is_encrypted:
            raise ValueError("PDF jest zabezpieczony hasłem. Wgraj plik bez hasła.")
        if len(dokument) > MAX_STRON:
            raise ValueError(f"PDF ma za dużo stron (maksymalnie {MAX_STRON}).")
        linie, skany, uzyto_ocr = [], [], False
        for nr, strona in enumerate(dokument, start=1):
            tekst = strona.get_text("text", sort=True)
            if len(tekst.strip()) < 30:
                uzyto_ocr = True
                skany.append((nr, strona.get_pixmap(matrix=fitz.Matrix(2.3, 2.3), alpha=False).tobytes("png")))
                if len(skany) == 8:
                    for numer, odczyt in _ocr_strony(skany).items():
                        linie.extend((numer, " ".join(l.split())) for l in odczyt.splitlines() if l.strip())
                    skany.clear()
            else:
                linie.extend((nr, " ".join(l.split())) for l in tekst.splitlines() if l.strip())
        if skany:
            for nr, tekst in _ocr_strony(skany).items():
                linie.extend((nr, " ".join(l.split())) for l in tekst.splitlines() if l.strip())
        if not linie:
            raise ValueError("PDF nie zawiera czytelnego tekstu.")
        linie.sort(key=lambda x: x[0])
        return linie, uzyto_ocr
    finally:
        dokument.close()


def odczytaj_tekst(zawartosc: bytes, nazwa: str) -> tuple[list[tuple[int, str]], bool]:
    if not zawartosc or len(zawartosc) > MAX_PLIK:
        raise ValueError("Plik jest pusty albo przekracza limit 50 MB.")
    rozszerzenie = Path(nazwa).suffix.lower()
    if rozszerzenie == ".docx":
        return _docx_linie(zawartosc), False
    if rozszerzenie == ".pdf":
        return _pdf_linie(zawartosc)
    raise ValueError("Obsługiwane są pliki .docx i .pdf.")
