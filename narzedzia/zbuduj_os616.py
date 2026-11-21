"""Buduje dwustronicowy druk OŚ-6165 z fotografii użytkownika."""
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
    s.top_margin, s.bottom_margin, s.left_margin, s.right_margin = Cm(1.8), Cm(1.8), Cm(2.0), Cm(2.0)
    normal = d.styles["Normal"]
    normal.font.name, normal.font.size = "Arial", Pt(11)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after, normal.paragraph_format.line_spacing = Pt(4), 1.05
    d.core_properties.title = "Wniosek OŚ-6165 o zaświadczenie dotyczące uproszczonego planu urządzenia lasu"
    d.core_properties.author = "Dokumenty FILAR"

    def p(txt="", size=None, bold=False, italic=False, align=None, before=0, after=4):
        a = d.add_paragraph()
        a.alignment = align
        a.paragraph_format.space_before, a.paragraph_format.space_after = Pt(before), Pt(after)
        r = a.add_run(txt)
        r.bold, r.italic = bold or None, italic or None
        if size: r.font.size = Pt(size)
        return a

    def linia(tekst, label="", size=12, after=8, bold=False):
        a = p("", after=after)
        r = a.add_run(tekst); r.bold = bold or None; r.underline = True
        if size: r.font.size = Pt(size)
        if label:
            q = a.add_run("\n" + label); q.italic = True; q.font.size = Pt(9)
        return a

    def wybor(kod, tekst):
        a = p("", after=3)
        styl = "OS616_ODBIOR_" + kod.upper()
        if styl not in d.styles: d.styles.add_style(styl, WD_STYLE_TYPE.CHARACTER)
        r = a.add_run("☐  "); r.style = styl; r.font.name = "Arial Unicode MS"; r.font.size = Pt(12)
        a.add_run(tekst)

    p("OŚ-6165", 11, align=WD_ALIGN_PARAGRAPH.RIGHT, after=13)
    p("{{ miejscowosc_data }}", 12, italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, after=13)
    linia("{{ wnioskodawca }}", "Imię i nazwisko oraz adres", after=8)
    linia("{{ telefon }}", "Nr telefonu", after=13)
    for text in ["Starostwo Powiatowe", "w Nowym Targu", "Wydział Ochrony Środowiska", "i Zasobów Naturalnych", "ul. Bolesława Wstydliwego 14", "34-400 Nowy Targ"]:
        p(text, 14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    p("", after=10)
    p("W N I O S E K", 15, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    p("O WYDANIE ZAŚWIADCZENIA CZY GRUNTY SĄ OBJĘTE UPROSZCZONYM\nPLANEM URZĄDZENIA LASU – DLA POTRZEB NOTARIALNYCH", 13, True, align=WD_ALIGN_PARAGRAPH.CENTER, after=15)
    a = p("Proszę o wydanie zaświadczenia, czy działka/i ewidencyjne o nr: ", 12, after=8)
    r = a.add_run("{{ dzialki }}"); r.underline = True
    a = p("położone w miejscowości: ", 12, after=8)
    r = a.add_run("{{ miejscowosc }}"); r.underline = True
    p("jest/są objęte uproszczonym planem urządzenia lasu lub decyzją wydaną w trybie art. 19 ust. 3 ustawy o lasach.", 12, after=19)
    p(".................................................................................................", align=WD_ALIGN_PARAGRAPH.RIGHT, after=0)
    p("Podpis", 10, align=WD_ALIGN_PARAGRAPH.RIGHT, after=14)
    p("Wydanie zaświadczenia podlega opłacie skarbowej w wysokości 17 zł płatnej na konto Urzędu Miasta Nowy Targ nr: 20 1240 6292 1111 0011 2118 2790.", 11, True, after=13)
    p("Sposób odbioru", 11, after=4)
    for kod, tekst in [("osobiscie_dzis", "Osobiście w dniu złożenia"), ("osobiscie_inny", "Osobiście w innym dniu"), ("poczta", "Przesyłka listowna")]:
        wybor(kod, tekst)

    d.add_page_break()
    rodo = (
        "Zgodnie z art. 13 ust. 1 i ust. 2 rozporządzenia Parlamentu Europejskiego i Rady (UE) 2016/679 z dnia 27 kwietnia 2016 r. w sprawie ochrony osób fizycznych w związku z przetwarzaniem danych osobowych i w sprawie swobodnego przepływu takich danych oraz uchylenia dyrektywy 95/46/WE (ogólne rozporządzenie o ochronie danych, RODO) (Dz. Urz. UE L 119/1) informujemy, że Administratorem Pani/Pana danych osobowych w związku z wykonaniem przez Powiat Nowotarski zadań publicznych w zakresie wydania zaświadczenia dotyczącego Uproszczonych Planów Urządzania Lasu w celach notarialnych jest Starostwo Powiatowe w Nowym Targu przy ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ. Szczegółowa klauzula informacyjna znajduje się na stronie internetowej Administratora w zakładce: https://www.nowotarski.pl/polityka-prywatnosci/dokumenty/polityka-prywatnosci-812.html"
    )
    a = p(rodo, 12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=2)
    a.paragraph_format.line_spacing = 1.15
    Path(cel).parent.mkdir(parents=True, exist_ok=True)
    d.save(cel)
    return Path(cel)


if __name__ == "__main__":
    print(zbuduj(sys.argv[1] if len(sys.argv) > 1 else ROOT / "szablony" / "os616_zaswiadczenie.docx"))
