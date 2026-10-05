"""Buduje ikonę programu ze źródłowej grafiki (ikona/zrodlo.webp, PNG/WebP z przezroczystym tłem):

- ikona/ikona.icns            ikona aplikacji „Dokumenty FILAR” na pulpicie (wstawia ją instaluj_mac.sh),
- app/static/ikona-64.png     logo w nagłówku programu i favicon,
- app/static/ikona-192.png    duża wersja (ekran wyłączenia, favicon w wysokiej rozdzielczości).

Po podmianie grafiki: .venv/bin/pip install pillow && .venv/bin/python narzedzia/zbuduj_ikone.py
(Pillow jest potrzebny tylko temu narzędziu, program działa bez niego.)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

KATALOG = Path(__file__).resolve().parent.parent
ZRODLO = KATALOG / "ikona" / "zrodlo.webp"
# Piksele bardziej przezroczyste niż ten próg to tylko poświata wokół ikony – nie wliczamy ich do kadru.
PROG_KRYCIA = 40
# Siatka ikon macOS: kafelek zajmuje 824 z 1024 px płótna, reszta to margines na cień systemu.
MACOS_PLOTNO, MACOS_KAFELEK = 1024, 824


def przytnij(obraz: Image.Image) -> Image.Image:
    """Kwadratowy kadr na nieprzezroczystą część ikony (bez pustego tła i słabej poświaty)."""
    maska = obraz.getchannel("A").point(lambda a: 255 if a > PROG_KRYCIA else 0)
    lewo, gora, prawo, dol = maska.getbbox()
    bok = max(prawo - lewo, dol - gora)
    srodek_x, srodek_y = (lewo + prawo) / 2, (gora + dol) / 2
    return obraz.crop((round(srodek_x - bok / 2), round(srodek_y - bok / 2),
                       round(srodek_x + bok / 2), round(srodek_y + bok / 2)))


def main(zrodlo: Path = ZRODLO) -> None:
    ikona = przytnij(Image.open(zrodlo).convert("RGBA"))

    for rozmiar in (64, 192):
        cel = KATALOG / "app" / "static" / f"ikona-{rozmiar}.png"
        ikona.resize((rozmiar, rozmiar), Image.LANCZOS).save(cel, optimize=True)
        print(f"Zapisano {cel.relative_to(KATALOG)}")

    plotno = Image.new("RGBA", (MACOS_PLOTNO, MACOS_PLOTNO), (0, 0, 0, 0))
    margines = (MACOS_PLOTNO - MACOS_KAFELEK) // 2
    plotno.paste(ikona.resize((MACOS_KAFELEK, MACOS_KAFELEK), Image.LANCZOS), (margines, margines))
    cel = KATALOG / "ikona" / "ikona.icns"
    plotno.save(cel, sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)])
    print(f"Zapisano {cel.relative_to(KATALOG)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ZRODLO)
