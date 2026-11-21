"""Odtwarza dwustronicowy formularz PB-9 ze zdjęć użytkownika."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(__file__).resolve().parent.parent


def zbuduj(cel):
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Cm(1.2), Cm(1.15), Cm(1.5), Cm(1.5)
    normal = d.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(9.0)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after, normal.paragraph_format.line_spacing = Pt(1), 1.0
    d.core_properties.title = "Wniosek o przeniesienie decyzji o pozwoleniu na budowę PB-9"
    d.core_properties.author = "Dokumenty FILAR"

    def p(txt="", size=None, bold=False, align=None, before=0, after=1, italic=False):
        a = d.add_paragraph()
        a.alignment = align
        a.paragraph_format.space_before, a.paragraph_format.space_after = Pt(before), Pt(after)
        r = a.add_run(txt)
        r.bold, r.italic = bold or None, italic or None
        if size:
            r.font.size = Pt(size)
        return a

    def sec(txt):
        a = p(txt, 10.5, True, before=3, after=1)
        a.paragraph_format.keep_with_next = True

    def field(label, key):
        a = p("", after=0)
        a.paragraph_format.keep_together = True
        if label:
            a.add_run(label + " ")
        r = a.add_run("{{ " + key + " }}")
        r.underline = True

    def box(label, key):
        a = p("☐ " + label, after=0)
        style = "PB9_" + key
        if style not in d.styles:
            d.styles.add_style(style, WD_STYLE_TYPE.CHARACTER)
        a.runs[0].style = style

    p("WNIOSEK", 17, True, WD_ALIGN_PARAGRAPH.CENTER, after=0)
    p("o przeniesienie decyzji o pozwoleniu na budowę", 13.2, True, WD_ALIGN_PARAGRAPH.CENTER, after=0)
    p("(PB-9)", 12, True, WD_ALIGN_PARAGRAPH.CENTER, after=4)
    p("Podstawa prawna: art. 40 ust. 1 w zw. z ust. 5 pkt 1 ustawy z dnia 7 lipca 1994 r. – Prawo budowlane (Dz. U. z 2025 r. poz. 418, 1080, 1535, 1673 i 1847).", after=4)
    sec("1. ORGAN ADMINISTRACJI ARCHITEKTONICZNO-BUDOWLANEJ")
    p("Nazwa:   Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ", after=3)
    sec("2.1. DANE NOWEGO INWESTORA¹)")
    for label, key in [
        ("Imię i nazwisko lub nazwa:", "inwestor.imie_nazwisko"), ("Kraj:", "inwestor.kraj"),
        ("Województwo:", "inwestor.wojewodztwo"), ("Powiat:", "inwestor.powiat"),
        ("Gmina:", "inwestor.gmina"), ("Ulica:", "inwestor.ulica"), ("Nr domu:", "inwestor.nr_domu"),
        ("Nr lokalu:", "inwestor.nr_lokalu"), ("Miejscowość:", "inwestor.miejscowosc"),
        ("Kod pocztowy:", "inwestor.kod_pocztowy"), ("E-mail (nieobowiązkowo):", "email"),
        ("Nr tel. (nieobowiązkowo):", "telefon"),
    ]:
        field(label, key)
    sec("2.2. DANE NOWEGO INWESTORA (DO KORESPONDENCJI)¹)")
    p("Wypełnia się, jeżeli adres do korespondencji inwestora jest inny niż wskazany w pkt 2.1.", 8.2, italic=True)
    for label, key in [
        ("Kraj:", "kraj"), ("Województwo:", "wojewodztwo"), ("Powiat:", "powiat"),
        ("Gmina:", "gmina"), ("Ulica:", "ulica"), ("Nr domu:", "nr_domu"),
        ("Nr lokalu:", "nr_lokalu"), ("Miejscowość:", "miejscowosc"),
        ("Kod pocztowy:", "kod_pocztowy"), ("Adres do doręczeń elektronicznych²):", "adres_elektroniczny"),
    ]:
        field(label, "korespondencja." + key)
    sec("3. DANE PEŁNOMOCNIKA / PEŁNOMOCNIKA DO DORĘCZEŃ¹)")
    p("Wypełnia się, jeżeli inwestor działa przez pełnomocnika.", 8.2, italic=True)
    a = p("", after=0)
    for key, label in [("pelnomocnik", "☐ pełnomocnik"), ("do_doreczen", "     ☐ pełnomocnik do doręczeń")]:
        style = "PB9_TYP_" + key
        if style not in d.styles:
            d.styles.add_style(style, WD_STYLE_TYPE.CHARACTER)
        a.add_run(label).style = style
    for label, key in [("Imię i nazwisko:", "proxy_nazwa"), ("Kraj:", "proxy.kraj"),
                       ("Województwo:", "proxy.wojewodztwo"), ("Powiat:", "proxy.powiat")]:
        field(label, key)

    d.add_page_break()
    for label, key in [("Gmina:", "proxy.gmina"), ("Ulica:", "proxy.ulica"), ("Nr domu:", "proxy.nr_domu"),
                       ("Nr lokalu:", "proxy.nr_lokalu"), ("Miejscowość:", "proxy.miejscowosc"),
                       ("Kod pocztowy:", "proxy.kod_pocztowy"), ("Adres do doręczeń elektronicznych²):", "proxy.adres_elektroniczny"),
                       ("E-mail (nieobowiązkowo):", "proxy.email"), ("Nr tel. (nieobowiązkowo):", "proxy.telefon")]:
        field(label, key)
    sec("4. DANE DOTYCHCZASOWEGO INWESTORA¹)")
    field("Imię i nazwisko lub nazwa:", "dotychczasowy_inwestor")
    sec("5. INFORMACJE O DECYZJI O POZWOLENIU NA BUDOWĘ")
    for label, key in [("Data wydania:", "data_decyzji"), ("Nr decyzji:", "nr_decyzji"),
                       ("Znak sprawy:", "znak_sprawy"), ("Nazwa zamierzenia budowlanego objętego decyzją:", "nazwa_zamierzenia")]:
        field(label, key)
    sec("6. OŚWIADCZENIE NOWEGO INWESTORA")
    p("Przejmuję na siebie warunki zawarte w decyzji, o której mowa w pkt 5.", after=2)
    sec("7. ZAŁĄCZNIKI")
    for key, label in [
        ("oswiadczenie", "Oświadczenie o posiadanym prawie do dysponowania nieruchomością na cele budowlane."),
        ("pelnomocnictwo", "Pełnomocnictwo do reprezentowania inwestora (opłacone zgodnie z ustawą z dnia 16 listopada 2006 r. o opłacie skarbowej (Dz. U. z 2025 r. poz. 1154, 1795 i 1847)) – jeżeli nowy inwestor działa przez pełnomocnika."),
        ("oplata", "Potwierdzenie uiszczenia opłaty skarbowej – jeżeli obowiązek uiszczenia takiej opłaty wynika z ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej."),
        ("zgoda", "Zgoda dotychczasowego inwestora, na rzecz którego decyzja została wydana³), ⁴)."),
    ]:
        box(label, "ZAL_" + key)
    sec("8. PODPIS NOWEGO INWESTORA (PEŁNOMOCNIKA) I DATA PODPISU")
    p("Podpis powinien być czytelny. Podpis i datę podpisu umieszcza się w przypadku składania wniosku w postaci papierowej.", 8.2)
    p("........................................................................................................................................", before=3, after=3)
    p("¹) W przypadku większej liczby inwestorów lub pełnomocników dane kolejnych inwestorów lub pełnomocników dodaje się w formularzu albo zamieszcza na osobnych stronach i dołącza do formularza.", 7.0)
    p("²) W przypadku określonym w art. 147 ust. 1 ustawy z dnia 18 listopada 2020 r. o doręczeniach elektronicznych (Dz. U. z 2026 r. poz. 3) w razie braku adresu do doręczeń elektronicznych wskazuje się adres skrzynki ePUAP. Możliwość doręczania korespondencji na skrzynkę ePUAP obowiązuje do dnia określonego w tym przepisie.", 7.0)
    p("³) Zgoda dotychczasowego inwestora nie jest wymagana, jeżeli własność nieruchomości lub uprawnienia wynikające z użytkowania wieczystego dotyczącego nieruchomości, objęte decyzją o pozwoleniu na budowę po wydaniu tego pozwolenia przeszły z dotychczasowego inwestora na nowego inwestora wnioskującego o przeniesienie pozwolenia na budowę.", 7.0)
    p("⁴) Zamiast oryginału można dołączyć kopię dokumentu.", 7.0)
    Path(cel).parent.mkdir(parents=True, exist_ok=True)
    d.save(cel)
    return Path(cel)


if __name__ == "__main__":
    print(zbuduj(sys.argv[1] if len(sys.argv) > 1 else ROOT / "szablony" / "pb9_wniosek.docx"))
