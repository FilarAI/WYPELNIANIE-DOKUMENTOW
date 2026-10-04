"""Buduje szablony biura (szablony/*.docx) od zera, wzorowane na dokumentach FILAR-USŁUGI.

Uruchomienie: .venv/bin/python narzedzia/zbuduj_szablony.py
Znaczniki {{ ... }} wypełnia app/generator.py (docxtpl).
Baner pełnomocnictwa: szablony/grafika/naglowek_filar.png (PNG na całą szerokość kartki, np. 2000 × 360 px).
Gdy pliku nie ma, pełnomocnictwo powstaje bez banera.
"""
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.image.image import Image as DocxImage
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SZABLONY = Path(__file__).resolve().parent.parent / "szablony"
SZARE_TLO = "D9D9D9"
GRAFIKA_NAGLOWKA = SZABLONY / "grafika" / "naglowek_filar.png"
STOPKA_NAZWA = "FILAR-USŁUGI adres: "
STOPKA_DANE = ("ul. Sądecka 33h/11, 34-700 Rabka-Zdrój, tel.: 695 770 613, 795 130 812, "
               "e-mail: biurofilarmf@gmail.com")
SZARY = RGBColor(0x59, 0x59, 0x59)


# ---------------------------------------------------------------- pomocnicze

def nowy_dokument(czcionka: str, rozmiar: float, marginesy: tuple[float, float, float, float]):
    """marginesy w cm: (góra, prawy, dół, lewy)."""
    d = docx.Document()
    styl = d.styles["Normal"]
    styl.font.name = czcionka
    styl.font.size = Pt(rozmiar)
    styl.element.rPr.rFonts.set(qn("w:eastAsia"), czcionka)
    styl.paragraph_format.space_after = Pt(0)
    styl.paragraph_format.line_spacing = 1.0
    sekcja = d.sections[0]
    sekcja.page_width, sekcja.page_height = Cm(21.0), Cm(29.7)
    sekcja.top_margin, sekcja.right_margin, sekcja.bottom_margin, sekcja.left_margin = (Cm(m) for m in marginesy)
    return d


def akapit(miejsce, *fragmenty, wyrownanie=None, przed=0, po=0, tlo=None, wciecie=None, rozmiar=None,
           pogrubienie=False):
    """fragmenty: teksty lub krotki (tekst, {"b": bool, "sup": bool, "size": pt}); "\\n" = złamanie linii."""
    p = miejsce.add_paragraph()
    if wyrownanie is not None:
        p.alignment = wyrownanie
    p.paragraph_format.space_before = Pt(przed)
    p.paragraph_format.space_after = Pt(po)
    if wciecie is not None:
        p.paragraph_format.left_indent = Cm(wciecie)
    if tlo:
        cieniuj(p._p.get_or_add_pPr(), tlo)
    for fragment in fragmenty:
        tekst, opcje = (fragment, {}) if isinstance(fragment, str) else fragment
        for nr, linia in enumerate(tekst.split("\n")):
            if nr:
                p.add_run().add_break(WD_BREAK.LINE)
            if not linia:
                continue
            r = p.add_run(linia)
            r.bold = opcje.get("b", pogrubienie) or None
            r.font.superscript = opcje.get("sup") or None
            if opcje.get("size") or rozmiar:
                r.font.size = Pt(opcje.get("size") or rozmiar)
    return p


def cieniuj(element_pr, kolor: str):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), kolor)
    element_pr.append(shd)


def stopka(d, rozmiar: float = 8):
    """Tekstowa stopka biura: szara, wyśrodkowana, z cienką linią nad tekstem."""
    p = d.sections[0].footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(3)
    obramowanie = OxmlElement("w:pBdr")
    gora = OxmlElement("w:top")
    for atrybut, wartosc in {"w:val": "single", "w:sz": "4", "w:space": "4", "w:color": "A6A6A6"}.items():
        gora.set(qn(atrybut), wartosc)
    obramowanie.append(gora)
    p._p.get_or_add_pPr().append(obramowanie)
    for tekst, pogrubiony in [(STOPKA_NAZWA, True), (STOPKA_DANE, False)]:
        r = p.add_run(tekst)
        r.bold = pogrubiony or None
        r.font.size = Pt(rozmiar)
        r.font.color.rgb = SZARY


def wysokosc_banera_cm(grafika: Path, szerokosc_cm: float = 21.0) -> float:
    obraz = DocxImage.from_file(str(grafika))
    return szerokosc_cm * obraz.px_height / obraz.px_width


def naglowek_z_grafika(d, grafika: Path, margines_lewy: float, margines_prawy: float):
    """Baner na całą szerokość kartki: ujemne wcięcia znoszą marginesy, więc nie trzeba pływającego obrazu."""
    sekcja = d.sections[0]
    sekcja.header_distance = Cm(0)
    p = sekcja.header.paragraphs[0]
    p.paragraph_format.left_indent = Cm(-margines_lewy)
    p.paragraph_format.right_indent = Cm(-margines_prawy)
    p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(grafika), width=sekcja.page_width)


# ---------------------------------------------------------------- PB-5

def pb5():
    d = nowy_dokument("Times New Roman", 10.5, (0.75, 1.8, 1.25, 1.8))

    # Nagłówek formularza na szarym tle
    tabela = d.add_table(rows=1, cols=1)
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    komorka = tabela.cell(0, 0)
    cieniuj(komorka._tc.get_or_add_tcPr(), SZARE_TLO)
    komorka.paragraphs[0]._p.getparent().remove(komorka.paragraphs[0]._p)
    akapit(komorka, "OŚWIADCZENIE", wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, przed=4, rozmiar=13, pogrubienie=True)
    akapit(komorka, "o posiadanym prawie do dysponowania nieruchomością na cele budowlane",
           wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, rozmiar=11, pogrubienie=True)
    akapit(komorka, "(PB-5)", wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, po=6, rozmiar=11, pogrubienie=True)
    akapit(komorka, ("Podstawa prawna", {"b": True}),
           ": Art. 32 ust. 4 pkt 2 ustawy z dnia 7 lipca 1994 r. – Prawo budowlane "
           "(Dz. U. z 2020 r. poz. 1333, z późn. zm.).", rozmiar=7.5, po=3, wciecie=0.3)
    akapit(komorka, ("Dodatkowe informacje: ", {"b": True}),
           "Prawo do dysponowania nieruchomością na cele budowlane jest to tytuł prawny wynikający z prawa "
           "własności, użytkowania wieczystego, zarządu, ograniczonego prawa rzeczowego albo stosunku "
           "zobowiązaniowego, przewidującego uprawnienia do wykonywania robót budowlanych.",
           wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, rozmiar=7.5, po=3, wciecie=0.3)
    akapit(komorka, "W przypadku, gdy do złożenia oświadczenia zobowiązanych jest kilka osób, każda z tych osób "
                    "składa oświadczenie oddzielnie na osobnym formularzu.",
           wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, rozmiar=7.5, po=4, wciecie=0.3)

    def naglowek_sekcji(*fragmenty):
        akapit(d, *fragmenty, przed=10, po=6, tlo=SZARE_TLO, pogrubienie=True)

    def linia(*fragmenty):
        akapit(d, *fragmenty, po=6, wciecie=0.5)

    naglowek_sekcji("1. DANE INWESTORA")
    linia("Imię i nazwisko lub nazwa: {{ inwestor.imie_nazwisko }}")
    linia("Kraj: {{ inwestor.kraj }} Województwo: {{ inwestor.wojewodztwo }} "
          "Powiat: {{ inwestor.powiat }} Gmina: {{ inwestor.gmina }}")
    linia("Ulica: {{ inwestor.ulica }} Nr domu: {{ inwestor.nr_domu }} Nr lokalu: {{ inwestor.nr_lokalu }}")
    linia("Miejscowość: {{ inwestor.miejscowosc }} Kod pocztowy: {{ inwestor.kod_pocztowy }} "
          "Poczta: {{ inwestor.poczta }}")

    naglowek_sekcji("2. DANE OSOBY UPOWAŻNIONEJ DO ZŁOŻENIA OŚWIADCZENIA W IMIENIU INWESTORA", ("1)", {"sup": True}))
    linia("Imię i nazwisko lub nazwa: {{ upowazniony.imie_nazwisko }}")
    linia("Kraj: {{ upowazniony.kraj }} Województwo: {{ upowazniony.wojewodztwo }}")
    linia("Powiat: {{ upowazniony.powiat }} Gmina: {{ upowazniony.gmina }}")
    linia("Ulica: {{ upowazniony.ulica }} Nr domu: {{ upowazniony.nr_domu }} Nr lokalu: {{ upowazniony.nr_lokalu }}")
    linia("Miejscowość: {{ upowazniony.miejscowosc }} Kod pocztowy: {{ upowazniony.kod_pocztowy }} "
          "Poczta: {{ upowazniony.poczta }}")

    naglowek_sekcji("3. DANE NIERUCHOMOŚCI", ("2)", {"sup": True}))
    linia("Województwo: {{ nieruchomosc.wojewodztwo }}")
    linia("Powiat: {{ nieruchomosc.powiat }} Gmina: {{ nieruchomosc.gmina }}")
    linia("Ulica: {{ nieruchomosc.ulica }} Nr domu: {{ nieruchomosc.nr_domu }}")
    linia("Miejscowość: {{ nieruchomosc.miejscowosc }} Kod pocztowy: {{ nieruchomosc.kod_pocztowy }}")
    linia("Identyfikator działki ewidencyjnej", ("3)", {"sup": True}), ": {{ nieruchomosc.identyfikator_dzialki }}")
    akapit(d, "Liczba stron zawierających dane o kolejnych nieruchomościach (załączanych do oświadczenia): ……",
           po=6, wciecie=0.5, rozmiar=9.5)

    akapit(d, "Po zapoznaniu się z art. 32 ust. 4 pkt 2 oraz art. 3 pkt 11 ustawy z dnia 7 lipca 1994 r. – Prawo "
              "budowlane oświadczam, że posiadam prawo do dysponowania nieruchomością (nieruchomościami) na cele "
              "budowlane określoną (określonymi) w pkt 3 tego oświadczenia.",
           wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, przed=10, po=4, tlo=SZARE_TLO, rozmiar=9.5)
    akapit(d, "Jestem świadomy (świadoma) odpowiedzialności karnej za podanie nieprawdy w niniejszym oświadczeniu, "
              "zgodnie z art. 233 ustawy z dnia 6 czerwca 1997 r. – Kodeks karny (Dz. U. z 2020 r. poz. 1444, "
              "z późn. zm.).", wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, po=4, tlo=SZARE_TLO, rozmiar=9.5)

    naglowek_sekcji("4. PODPIS INWESTORA LUB OSOBY UPOWAŻNIONEJ DO ZŁOŻENIA OŚWIADCZENIA W IMIENIU INWESTORA "
                    "I DATA PODPISU")
    akapit(d, "Podpis powinien być czytelny.", po=28, rozmiar=7.5)
    akapit(d, "……………………………………………………………………………………………………")

    akapit(d, "Objaśnienia:", przed=24, po=2, rozmiar=7.5, pogrubienie=True)
    for przypis in [
        "1) Wypełnia się, jeżeli oświadczenie jest składane w imieniu osoby prawnej lub jednostki organizacyjnej "
        "nieposiadającej osobowości prawnej albo oświadczenie w imieniu inwestora składa jego pełnomocnik.",
        "2) W przypadku większej liczby nieruchomości dane kolejnych nieruchomości dodaje się w formularzu albo "
        "zamieszcza na osobnych stronach i dołącza do formularza.",
        "3) W przypadku oświadczenia sporządzanego w postaci papierowej zamiast identyfikatora działki ewidencyjnej "
        "można wskazać obręb ewidencyjny i nr działki ewidencyjnej oraz arkusz mapy, jeżeli występuje.",
    ]:
        akapit(d, przypis, wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, po=1, rozmiar=7.5)

    d.save(SZABLONY / "pb5_oswiadczenie.docx")


# ---------------------------------------------------------------- Pełnomocnictwo

def pelnomocnictwo(cel: Path = SZABLONY / "pelnomocnictwo.docx", grafika: Path = GRAFIKA_NAGLOWKA):
    z_banerem = grafika.is_file()
    # Z banerem tekst zaczyna się 0,6 cm pod nim (wysokość banera z proporcji obrazu przy szerokości 21 cm).
    gora = wysokosc_banera_cm(grafika) + 0.6 if z_banerem else 2.5
    d = nowy_dokument("Arial Narrow", 12, (gora, 1.75, 1.5, 2.5))
    sekcja = d.sections[0]
    sekcja.footer_distance = Cm(0.8)
    if z_banerem:
        naglowek_z_grafika(d, grafika, margines_lewy=2.5, margines_prawy=1.75)

    akapit(d, "Rabka-Zdrój {{ data }}", wyrownanie=WD_ALIGN_PARAGRAPH.RIGHT, po=36)
    akapit(d, "Pełnomocnictwo", wyrownanie=WD_ALIGN_PARAGRAPH.CENTER, po=30, rozmiar=20, pogrubienie=True)

    akapit(d, "{{ ja }} {{ mocodawcy }}", po=6)
    akapit(d, "{{ zamieszkaly }}: {{ adres_mocodawcy }}", po=12)
    akapit(d, "{{ udzielam }} pełnomocnictwa ", ("Bartłomiejowi Filar", {"b": True}), po=6)
    akapit(d, "zam. 34-700 Rabka-Zdrój ul. Sądecka 33h/11 do {{ mnie }} jako {{ inwestora }} w sprawie wszelkich "
              "formalności oraz do występowania w {{ moim }} imieniu przed organami administracji publicznej "
              "związanych z:", wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, po=12)
    akapit(d, "Uzyskaniem wszelkich uzgodnień i decyzji w związku z realizacją inwestycji „{{ nazwa_inwestycji }}”",
           po=12, rozmiar=14, pogrubienie=True)
    akapit(d, "w miejscowości:", po=6)
    akapit(d, "{{ lokalizacja }}", po=18, rozmiar=14, pogrubienie=True)
    akapit(d, "{{ upowazniam }} pełnomocnika do składania wszelkich oświadczeń, wniosków, podań, odwołań, skarg oraz "
              "zażaleń, jak również do odbioru i kwitowania odbioru dokumentów, korespondencji, prawa do zrzeczenia "
              "się od odwołania od wydanej decyzji, oraz do wszystkich innych czynności, jakie okażą się niezbędne "
              "do wykonania niniejszego pełnomocnictwa.", wyrownanie=WD_ALIGN_PARAGRAPH.JUSTIFY, po=48, rozmiar=13)
    akapit(d, "{{ podpisy }}", wyrownanie=WD_ALIGN_PARAGRAPH.RIGHT)

    stopka(d)
    d.save(cel)
    return z_banerem


if __name__ == "__main__":
    SZABLONY.mkdir(exist_ok=True)
    pb5()
    z_banerem = pelnomocnictwo()
    print(f"Zapisano szablony w {SZABLONY}" + ("" if z_banerem else f" (bez banera – brak pliku {GRAFIKA_NAGLOWKA})"))
