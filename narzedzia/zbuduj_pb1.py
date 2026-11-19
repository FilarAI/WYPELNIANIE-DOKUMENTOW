"""Tworzy dwustronicowy szablon wniosku PB-1 na podstawie zdjęć użytkownika."""
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
    s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Cm(1.15), Cm(1.1), Cm(1.5), Cm(1.5)
    normal = d.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(9)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after, normal.paragraph_format.line_spacing = Pt(1), 1.0
    d.core_properties.title = "Wniosek o pozwolenie na budowę PB-1"
    d.core_properties.author = "Dokumenty FILAR"

    def p(txt="", size=None, bold=False, align=None, before=0, after=1, italic=False):
        a = d.add_paragraph()
        a.alignment = align
        a.paragraph_format.space_before, a.paragraph_format.space_after = Pt(before), Pt(after)
        r = a.add_run(txt)
        r.bold, r.italic = bold or None, italic or None
        if size: r.font.size = Pt(size)
        return a

    def sec(txt):
        a = p(txt, 10.5, True, before=3, after=1)
        a.paragraph_format.keep_with_next = True

    def field(label, key):
        a = p("", after=0)
        a.paragraph_format.keep_together = True
        if label: a.add_run(label + " ")
        a.add_run("{{ " + key + " }}").underline = True

    def box(label, prefix, key):
        a = p("☐ " + label, after=0)
        style = prefix + key.upper()
        if style not in d.styles: d.styles.add_style(style, WD_STYLE_TYPE.CHARACTER)
        a.runs[0].style = style

    p("WNIOSEK", 17, True, WD_ALIGN_PARAGRAPH.CENTER, after=0)
    p("o pozwolenie na budowę", 13.2, True, WD_ALIGN_PARAGRAPH.CENTER, after=0)
    p("(PB-1)", 12, True, WD_ALIGN_PARAGRAPH.CENTER, after=4)
    p("Podstawa prawna: art. 28 ust. 1 w zw. z art. 32 i art. 33 ust. 2 i 2c ustawy z dnia 7 lipca 1994 r. – Prawo budowlane (Dz. U. z 2025 r. poz. 418, 1080, 1535, 1673 i 1847).", after=3)
    sec("1. ORGAN ADMINISTRACJI ARCHITEKTONICZNO-BUDOWLANEJ")
    p("Nazwa:   Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ", after=2)
    sec("2.1. DANE INWESTORA¹)")
    for label, key in [("Imię i nazwisko lub nazwa:","inwestor.imie_nazwisko"),("Kraj:","inwestor.kraj"),("Województwo:","inwestor.wojewodztwo"),("Powiat:","inwestor.powiat"),("Gmina:","inwestor.gmina"),("Ulica:","inwestor.ulica"),("Nr domu:","inwestor.nr_domu"),("Nr lokalu:","inwestor.nr_lokalu"),("Miejscowość:","inwestor.miejscowosc"),("Kod pocztowy:","inwestor.kod_pocztowy"),("E-mail (nieobowiązkowo):","email"),("Nr tel. (nieobowiązkowo):","telefon")]: field(label,key)
    sec("2.2. DANE INWESTORA (DO KORESPONDENCJI)¹)")
    p("Wypełnia się, jeżeli adres do korespondencji inwestora jest inny niż wskazany w pkt 2.1.", 8.2, italic=True)
    for label,key in [("Kraj:","kraj"),("Województwo:","wojewodztwo"),("Powiat:","powiat"),("Gmina:","gmina"),("Ulica:","ulica"),("Nr domu:","nr_domu"),("Nr lokalu:","nr_lokalu"),("Miejscowość:","miejscowosc"),("Kod pocztowy:","kod_pocztowy"),("Adres do doręczeń elektronicznych²):","adres_elektroniczny")]: field(label,"korespondencja."+key)
    sec("3. DANE PEŁNOMOCNIKA / PEŁNOMOCNIKA DO DORĘCZEŃ¹)")
    p("Wypełnia się, jeżeli inwestor działa przez pełnomocnika.", 8.2, italic=True, after=0)
    a=p("",after=0)
    for key,label in [("pelnomocnik","☐ pełnomocnik"),("do_doreczen","     ☐ pełnomocnik do doręczeń")]:
        style="PB1_PEL_"+key.upper()
        if style not in d.styles: d.styles.add_style(style,WD_STYLE_TYPE.CHARACTER)
        a.add_run(label).style=style
    for label,key in [("Imię i nazwisko:","proxy_nazwa"),("Kraj:","proxy.kraj"),("Województwo:","proxy.wojewodztwo"),("Powiat:","proxy.powiat"),("Gmina:","proxy.gmina"),("Ulica:","proxy.ulica"),("Nr domu:","proxy.nr_domu")]: field(label,key)

    d.add_page_break()
    for label,key in [("Nr lokalu:","proxy.nr_lokalu"),("Miejscowość:","proxy.miejscowosc"),("Kod pocztowy:","proxy.kod_pocztowy"),("Adres do doręczeń elektronicznych²):","proxy.adres_elektroniczny"),("E-mail (nieobowiązkowo):","proxy.email"),("Nr tel. (nieobowiązkowo):","proxy.telefon")]: field(label,key)
    sec("4. RODZAJ ZAMIERZENIA BUDOWLANEGO")
    p("Należy wskazać właściwe. Jeżeli zamierzenie obejmuje kilka rodzajów robót budowlanych, należy wskazać wszystkie właściwe.",8.2)
    for key,label in [("budowa","Budowa nowego obiektu budowlanego."),("rozbudowa","Rozbudowa istniejącego obiektu budowlanego."),("nadbudowa","Nadbudowa istniejącego obiektu budowlanego."),("odbudowa","Odbudowa obiektu budowlanego."),("inne_roboty","Wykonanie robót budowlanych innych niż wymienione.")]: box(label,"PB1_TYP_",key)
    sec("5. NAZWA ZAMIERZENIA BUDOWLANEGO³)")
    field("","nazwa")
    sec("6. DANE NIERUCHOMOŚCI (MIEJSCE WYKONYWANIA ROBÓT BUDOWLANYCH)¹)")
    for label,key in [("Województwo:","wojewodztwo"),("Powiat:","powiat"),("Gmina:","gmina"),("Ulica:","ulica"),("Nr domu:","nr_domu"),("Miejscowość:","miejscowosc"),("Kod pocztowy:","kod_pocztowy"),("Identyfikator działki ewidencyjnej⁴):","identyfikator_dzialki")]: field(label,"nieruchomosc."+key)
    sec("7. ZAŁĄCZNIKI")
    for key,label in [("oswiadczenie","Oświadczenie o posiadanym prawie do dysponowania nieruchomością na cele budowlane."),("pelnomocnictwo","Pełnomocnictwo do reprezentowania inwestora (opłacone zgodnie z ustawą z dnia 16 listopada 2006 r. o opłacie skarbowej (Dz. U. z 2025 r. poz. 1154, 1795 i 1847)) – jeżeli inwestor działa przez pełnomocnika."),("oplata","Potwierdzenie uiszczenia opłaty skarbowej – jeżeli obowiązek uiszczenia takiej opłaty wynika z ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej."),("projekt","Projekt zagospodarowania działki lub terenu oraz projekt architektoniczno-budowlany (w postaci papierowej w 3 egzemplarzach albo w postaci elektronicznej)."),("warunki","Decyzja o warunkach zabudowy i zagospodarowania terenu – jeżeli jest ona wymagana zgodnie z przepisami o planowaniu i zagospodarowaniu przestrzennym⁵)."),("inne","Inne (wymagane przepisami prawa):")]: box(label,"PB1_ZAL_",key)
    field("","zal_opis")
    sec("8. PODPIS INWESTORA (PEŁNOMOCNIKA) I DATA PODPISU")
    p("Podpis powinien być czytelny. Podpis i datę podpisu umieszcza się w przypadku składania wniosku w postaci papierowej.",8.2)
    p("........................................................................................................................................",before=2,after=3)
    p("¹) W przypadku większej liczby inwestorów, pełnomocników lub nieruchomości dane kolejnych inwestorów, pełnomocników lub nieruchomości dodaje się w formularzu albo zamieszcza na osobnych stronach i dołącza do formularza.",7)
    p("²) W przypadku określonym w art. 147 ust. 1 ustawy z dnia 18 listopada 2020 r. o doręczeniach elektronicznych (Dz. U. z 2026 r. poz. 3) w razie braku adresu do doręczeń elektronicznych wskazuje się adres skrzynki ePUAP. Możliwość doręczania korespondencji na skrzynkę ePUAP obowiązuje do dnia określonego w tym przepisie.",7)
    p("³) Nazwa powinna w sposób ogólny określać zamierzenie budowlane, np. „Zespół budynków jednorodzinnych wraz z infrastrukturą”.",7)
    p("⁴) W przypadku formularza w postaci papierowej zamiast identyfikatora działki ewidencyjnej można wskazać jednostkę ewidencyjną, obręb ewidencyjny i numer działki ewidencyjnej oraz arkusz mapy, jeżeli występuje.",7)
    p("⁵) Zamiast oryginału można dołączyć kopię dokumentu.",7)
    Path(cel).parent.mkdir(parents=True,exist_ok=True); d.save(cel); return Path(cel)

if __name__ == "__main__": print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/"szablony"/"pb1_wniosek.docx"))
