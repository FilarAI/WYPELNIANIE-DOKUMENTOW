"""Wygląd wyłącznie danych dopisywanych do dokumentów Word."""
from __future__ import annotations

from copy import deepcopy
import re

from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

GRANAT = "1F3864"
DOMYSLNE = {"rozmiar": "normalny", "pogrubienie": False, "kolor": "czarny"}
POLE_SZABLONU = re.compile(r"{{\s*([a-z_][a-z0-9_.]*)\s*}}")
FORMY_GRAMATYCZNE = {"ja", "zamieszkaly", "udzielam", "mnie", "inwestora", "moim", "upowazniam"}


def sprawdz(ustawienia: dict) -> dict:
    if (not isinstance(ustawienia, dict)
            or ustawienia.get("rozmiar") not in {"normalny", "wiekszy"}
            or type(ustawienia.get("pogrubienie")) is not bool
            or ustawienia.get("kolor") not in {"czarny", "granatowy"}):
        raise ValueError("Niepoprawne ustawienia wyglądu uzupełnionych danych.")
    return {k: ustawienia[k] for k in DOMYSLNE}


def odczytaj_z_formularza(formularz) -> dict:
    for nazwa in ("format-rozmiar", "format-pogrubienie", "format-kolor"):
        if len(formularz.getlist(nazwa)) > 1:
            raise ValueError("Niepoprawne ustawienia wyglądu uzupełnionych danych.")
    pogrubienie = formularz.get("format-pogrubienie", "")
    if pogrubienie not in {"", "tak"}:
        raise ValueError("Niepoprawne ustawienia wyglądu uzupełnionych danych.")
    return sprawdz({"rozmiar": formularz.get("format-rozmiar", "normalny"),
                    "pogrubienie": pogrubienie == "tak",
                    "kolor": formularz.get("format-kolor", "czarny")})


def z_danych(dane: dict) -> dict:
    return sprawdz(dane.get("formatowanie", DOMYSLNE))


def _rozmiar(r: Run) -> float:
    if r.font.size is not None:
        return r.font.size.pt
    for poczatek in (r.style, r._parent.style):
        styl, widziane = poczatek, set()
        while styl is not None and styl.style_id not in widziane:
            widziane.add(styl.style_id)
            if styl.font.size is not None:
                return styl.font.size.pt
            styl = styl.base_style
    return 11  # Domyślny rozmiar, gdy wzór nie określa go także w stylach.


def zastosuj(r: Run, ustawienia: dict | None) -> None:
    if ustawienia is None or not r.text.strip():
        return
    if ustawienia["rozmiar"] == "wiekszy":
        r.font.size = Pt(_rozmiar(r) + 2)
    if ustawienia["pogrubienie"]:
        r.bold = True
    r.font.color.rgb = RGBColor.from_string(GRANAT if ustawienia["kolor"] == "granatowy" else "000000")


def zastap(akapit: Paragraph, poczatek: int, koniec: int, wartosc: str,
           ustawienia: dict | None = None) -> None:
    """Izoluje wpisywaną wartość; litery przed nią i po niej zachowują format wzoru."""
    przebieg, dotkniete = 0, []
    for r in akapit.runs:
        koniec_runu = przebieg + len(r.text)
        if przebieg < koniec and koniec_runu > poczatek:
            dotkniete.append((r, max(0, poczatek - przebieg), min(len(r.text), koniec - przebieg)))
        przebieg = koniec_runu
    if not dotkniete:
        return
    pierwszy, od, do = dotkniete[0]
    ostatni, _, do_ostatniego = dotkniete[-1]
    przed, po = pierwszy.text[:od], ostatni.text[do_ostatniego:]
    nowy = Run(deepcopy(pierwszy._r), akapit)
    nowy.text = wartosc
    pierwszy._r.addnext(nowy._r)
    if len(dotkniete) == 1:
        if po:
            ogon = Run(deepcopy(pierwszy._r), akapit)
            ogon.text = po
            nowy._r.addnext(ogon._r)
        pierwszy.text = przed
    else:
        pierwszy.text = przed
        for r, _, _ in dotkniete[1:-1]:
            r.text = ""
        ostatni.text = po
    zastosuj(nowy, ustawienia)


def _akapity(dokument):
    yield from (Paragraph(p, dokument) for p in dokument.element.body.iter(qn("w:p")))
    widziane = set()
    for sekcja in dokument.sections:
        for czesc in (sekcja.header, sekcja.footer):
            if czesc.part.partname in widziane:
                continue
            widziane.add(czesc.part.partname)
            yield from (Paragraph(p, czesc) for p in czesc._element.iter(qn("w:p")))


def przygotuj_szablon(dokument, kontekst: dict, ustawienia: dict) -> None:
    """Rozdziela etykiety i znaczniki Jinja przed renderowaniem, bez wyszukiwania danych po treści."""
    for akapit in _akapity(dokument):
        for oryginal in list(akapit.runs):
            trafienia = list(POLE_SZABLONU.finditer(oryginal.text))
            if not trafienia:
                continue
            tekst, poprzedni, pozycja = oryginal.text, oryginal._r, 0
            for m in trafienia:
                if m.start() > pozycja:
                    staly = Run(deepcopy(oryginal._r), akapit)
                    staly.text = tekst[pozycja:m.start()]
                    poprzedni.addnext(staly._r)
                    poprzedni = staly._r
                r = Run(deepcopy(oryginal._r), akapit)
                r.text = m.group(0)
                wartosc = kontekst
                for czesc in m.group(1).split("."):
                    wartosc = wartosc.get(czesc, "") if isinstance(wartosc, dict) else ""
                if m.group(1) == "podpisy":
                    # Linie podpisów i etykieta Podpis zachowują wygląd wzoru.
                    from docxtpl import RichText
                    podpisy = RichText()
                    for nr, linia in enumerate(str(wartosc).split("\n")):
                        if nr:
                            podpisy.add("\n")
                        fragment = Run(deepcopy(oryginal._r), akapit)
                        fragment.text = linia
                        if linia.strip() and linia != "Podpis" and not re.fullmatch(r"[.…]+", linia):
                            zastosuj(fragment, ustawienia)
                        podpisy.xml += fragment._r.xml
                    kontekst["filar_podpisy"] = podpisy
                    r.text = "{{r filar_podpisy }}"
                elif (m.group(1) not in FORMY_GRAMATYCZNE and str(wartosc).strip()
                      and not re.fullmatch(r"[.…–—\s]+", str(wartosc))):
                    zastosuj(r, ustawienia)
                poprzedni.addnext(r._r)
                poprzedni = r._r
                pozycja = m.end()
            if pozycja < len(tekst):
                staly = Run(deepcopy(oryginal._r), akapit)
                staly.text = tekst[pozycja:]
                poprzedni.addnext(staly._r)
            oryginal._r.getparent().remove(oryginal._r)
