"""Zapis wygenerowanych dokumentów do folderu wybranego przez użytkownika (macOS).

Ostatnio użyty folder jest zapamiętywany w ~/.dokumenty_filar.json (poza repozytorium),
ścieżkę pliku ustawień można zmienić zmienną środowiskową DOKUMENTY_FILAR_USTAWIENIA (testy).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _plik_ustawien() -> Path:
    return Path(os.environ.get("DOKUMENTY_FILAR_USTAWIENIA", Path.home() / ".dokumenty_filar.json"))


def _ustawienia() -> dict:
    try:
        return json.loads(_plik_ustawien().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ostatni_folder() -> str:
    """Ostatnio użyty folder, jeśli nadal istnieje; w przeciwnym razie Pobrane (lub katalog domowy)."""
    zapamietany = _ustawienia().get("folder_zapisu", "")
    if zapamietany and Path(zapamietany).is_dir():
        return zapamietany
    pobrane = Path.home() / "Downloads"
    return str(pobrane if pobrane.is_dir() else Path.home())


def zapamietaj_folder(folder: str) -> None:
    ustawienia = _ustawienia() | {"folder_zapisu": folder}
    try:
        _plik_ustawien().write_text(json.dumps(ustawienia, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # brak zapamiętania nie blokuje zapisu dokumentów


def sprawdz_folder(folder: str) -> Path:
    """Zwraca ścieżkę folderu albo rzuca ValueError z komunikatem dla użytkownika."""
    if not folder.strip():
        raise ValueError("Wybierz folder, w którym mają zostać zapisane dokumenty.")
    sciezka = Path(folder.strip()).expanduser()
    if not sciezka.is_absolute() or not sciezka.is_dir():
        raise ValueError(f"Folder „{folder}” nie istnieje. Wybierz go ponownie przyciskiem „Wybierz…”.")
    return sciezka


def _wolna_nazwa(folder: Path, nazwa: str) -> Path:
    """Nie nadpisuje istniejących plików: Pelnomocnictwo_X.docx → Pelnomocnictwo_X (2).docx."""
    cel = folder / nazwa
    nr = 2
    while cel.exists():
        cel = folder / f"{Path(nazwa).stem} ({nr}){Path(nazwa).suffix}"
        nr += 1
    return cel


def zapisz_pliki(folder: Path, pliki: dict[str, bytes]) -> list[Path]:
    zapisane = []
    for nazwa, zawartosc in pliki.items():
        cel = _wolna_nazwa(folder, nazwa)
        cel.write_bytes(zawartosc)
        zapisane.append(cel)
    return zapisane


def wybierz_folder_w_oknie(poczatkowy: str = "") -> str | None:
    """Otwiera systemowe okno wyboru folderu (macOS). Zwraca ścieżkę albo None po anulowaniu."""
    if sys.platform != "darwin":
        raise RuntimeError("Okno wyboru folderu działa tylko na macOS – wpisz ścieżkę ręcznie.")
    domyslny = ""
    if poczatkowy and Path(poczatkowy).is_dir():
        domyslny = f' default location (POSIX file "{poczatkowy.replace(chr(34), "")}")'
    skrypt = f'activate\nPOSIX path of (choose folder with prompt "Gdzie zapisać dokumenty?"{domyslny})'
    wynik = subprocess.run(["osascript", "-e", skrypt], capture_output=True, text=True, timeout=600)
    if wynik.returncode != 0:
        return None  # anulowano (błąd -128) lub okno się nie otworzyło
    return wynik.stdout.strip().rstrip("/") or "/"


def pokaz_w_finderze(sciezka: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(sciezka)], check=False)
