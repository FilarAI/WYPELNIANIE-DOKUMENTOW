"""Odtwarza druk zgłoszenia zmian EGiB ze zdjęcia użytkownika z 19.11.2026."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent


def zbuduj(cel):
    d = Document(); sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.4), Cm(1.2)
    sec.left_margin = sec.right_margin = Cm(1.7)
    for name in ['Normal', 'Title']:
        st = d.styles[name]; st.font.name = 'Arial'; st.font.size = Pt(10)
        st.font.color.rgb = RGBColor(0, 0, 0)
        st.paragraph_format.line_spacing = 1.0; st.paragraph_format.space_after = Pt(2)
        for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    d.core_properties.title = 'Zgłoszenie zmian danych ewidencji gruntów i budynków'
    d.core_properties.author = 'Dokumenty FILAR'

    def p(text='', align=None, size=10, bold=False, italic=False, before=0, after=2, style=None, parent=None):
        obj = parent or d
        a = obj.add_paragraph(style=style)
        a.alignment = align; a.paragraph_format.space_before = Pt(before); a.paragraph_format.space_after = Pt(after)
        r = a.add_run(text); r.font.name = 'Arial'; r.font.size = Pt(size); r.bold = bold or None; r.italic = italic or None
        return a

    def table(cols=1):
        t = d.add_table(rows=1, cols=cols); t.autofit = False
        b = OxmlElement('w:tblBorders')
        for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
            e = OxmlElement('w:' + side); e.set(qn('w:val'), 'nil'); b.append(e)
        t._tbl.tblPr.append(b)
        for cell in t.rows[0].cells:
            mar = OxmlElement('w:tcMar')
            for side in ['top', 'bottom', 'left', 'right']:
                e = OxmlElement('w:' + side); e.set(qn('w:w'), '0'); e.set(qn('w:type'), 'dxa'); mar.append(e)
            cell._tc.get_or_add_tcPr().append(mar)
        return t

    p('{{ miejsce_data }}', WD_ALIGN_PARAGRAPH.RIGHT, after=10)
    t = table(2); t.columns[0].width = Cm(8.4); t.columns[1].width = Cm(9.2)
    left, right = t.rows[0].cells
    a = left.paragraphs[0]; a.paragraph_format.space_after = Pt(5)
    r = a.add_run('{{ zglaszajacy }}'); r.font.name = 'Arial'; r.font.size = Pt(10)
    for text in ['{{ adres1 }}', '{{ adres2 }}', '{{ telefon }}', '{{ email }}']:
        p(text, after=5, parent=left)
    p('(zgłaszający zmianę: imię i nazwisko, adres korespondencyjny,', size=8, align=WD_ALIGN_PARAGRAPH.CENTER, after=0, parent=left)
    p('numer telefonu, adres e-mail)', size=8, align=WD_ALIGN_PARAGRAPH.CENTER, parent=left)
    right.paragraphs[0].paragraph_format.space_after = Pt(14)
    for line in ['Starostwo Powiatowe w Nowym Targu', 'Wydział Geodezji, Katastru i Kartografii', 'ul. Bolesława Wstydliwego 14', '34-400 Nowy Targ']:
        p(line, WD_ALIGN_PARAGRAPH.CENTER, size=11.5, bold=True, italic=True, parent=right)
    p('ZGŁOSZENIE ZMIAN DANYCH', WD_ALIGN_PARAGRAPH.CENTER, size=14, bold=True, italic=True, before=14, after=1, style='Title')
    p('ewidencji gruntów i budynków', WD_ALIGN_PARAGRAPH.CENTER, size=13, bold=True, italic=True, after=15)
    p('Określenie nieruchomości, w której nastąpiły zmiany:', italic=True, size=11, after=4)
    p('{{ gmina }}', WD_ALIGN_PARAGRAPH.RIGHT, after=0)
    p('(nazwa jednostki ewidencyjnej - gmina)', WD_ALIGN_PARAGRAPH.RIGHT, italic=True, size=9, after=9)
    p('{{ obreb }}', WD_ALIGN_PARAGRAPH.RIGHT, after=0)
    p('(nazwa obrębu ewidencyjnego - miejscowość)', WD_ALIGN_PARAGRAPH.RIGHT, italic=True, size=9, after=10)
    p('Numery działek ewid. {{ dzialki }}', italic=True, size=11, after=8)
    a = p('Jako ', italic=True, size=10.5, after=4)
    for key, text in [('wlasciciel', 'właściciel'), ('separator', '/'), ('wladajacy', 'władający*')]:
        r = a.add_run(text); r.font.name = 'Arial'; r.font.size = Pt(10.5); r.italic = True
        if key != 'separator':
            name = 'EGiB_' + key; d.styles.add_style(name, WD_STYLE_TYPE.CHARACTER); r.style = name
    r = a.add_run(' ww. nieruchomością zgłaszam/y następujące zmiany danych ewidencyjnych:'); r.font.name = 'Arial'; r.font.size = Pt(10.5); r.italic = True
    t = table(); t.rows[0].height = Pt(82); t.rows[0].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    t.cell(0,0).paragraphs[0].add_run('{{ opis_zmian }}').font.name = 'Arial'
    p('Do zgłoszenia załączam/y:', italic=True, size=11, before=5, after=3)
    t = table(); t.rows[0].height = Pt(36); t.rows[0].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
    t.cell(0,0).paragraphs[0].add_run('{{ zalaczniki }}').font.name = 'Arial'

    a = p('Klauzula informacyjna administratora danych osobowych', WD_ALIGN_PARAGRAPH.CENTER, size=8, bold=True, italic=True, before=7, after=2)
    a.runs[0].underline = True
    p('Zgodnie z art. 13 ust. 1 i ust. 2 ogólnego rozporządzenia o ochronie danych z dnia 27 kwietnia 2016 (UE) 2016/679 dalej zwane RODO informujemy:', size=7, italic=True, after=1)
    for text in [
        '1. Administratorem Pani/Pana danych osobowych przetwarzanych w Starostwie Powiatowym w Nowym Targu jest Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ.',
        '2. Administrator wyznaczył Inspektora Ochrony Danych, z którym można się skontaktować za pomocą poczty elektronicznej: iod@nowotarski.pl lub telefonicznie (18) 266 13 34.',
        '3. Podanie przez Panią/Pana danych osobowych wynika z przepisów prawa i jest niezbędne do wypełnienia obowiązku prawnego ciążącego na administratorze (art. 6 ust. 1 lit. c RODO).',
        '4. Na zasadach określonych w RODO posiada Pani/Pan prawo dostępu do treści swoich danych, ich sprostowania, usunięcia, ograniczenia przetwarzania, prawo do przenoszenia danych i prawo wniesienia sprzeciwu, prawo wniesienia skargi do organu nadzorczego.'
    ]:
        a = p(text, size=7, italic=True, after=1); a.paragraph_format.left_indent = Cm(.4); a.paragraph_format.first_line_indent = Cm(-.4)
    p('Pełna treść klauzuli informacyjnej zamieszczona jest na stronie internetowej Starostwa Powiatowego pod adresem www.nowotarski.pl oraz w siedzibie Urzędu na tablicach ogłoszeń.', size=7, italic=True, after=8)
    a = p(after=9); a.paragraph_format.left_indent = Cm(.7); a.paragraph_format.first_line_indent = Cm(-.7)
    d.styles.add_style('EGiB_zgoda', WD_STYLE_TYPE.CHARACTER)
    r = a.add_run('☐'); r.style = 'EGiB_zgoda'; r.font.name = 'Arial Unicode MS'; r.font.size = Pt(15)
    r = a.add_run(' Wyrażam/y zgodę na przesłanie zawiadomienia o zmianach danych ewidencyjnych w postaci dokumentów elektronicznych w rozumieniu przepisów ustawy z dnia 17 lutego 2005r. o informatyzacji działalności podmiotów realizujących zadania publiczne (Dz. U. 2025, poz. 1703) za pomocą środków komunikacji elektronicznej w rozumieniu przepisów ustawy z dnia 18 lipca 2002 r. o świadczeniu usług drogą elektroniczną na podany w/w adres poczty elektronicznej, stosownie do § 35 pkt 5 rozporządzenia MRiT w sprawie ewidencji gruntów i budynków (Dz. U. 2024, poz. 219 z późn. zm.).')
    r.font.name = 'Times New Roman'; r.font.size = Pt(10.5)
    t = table(2); t.columns[0].width=Cm(5.7);t.columns[1].width=Cm(11.9)
    for cell, text, caption in [(t.cell(0,0), '{{ data }}', '(data)'), (t.cell(0,1), '.'*95, '(czytelny podpis zgłaszającego zmianę)')]:
        a = cell.paragraphs[0]; a.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=a.add_run(text);r.font.name='Arial';r.font.size=Pt(10)
        p(caption,WD_ALIGN_PARAGRAPH.CENTER,size=9,italic=True,parent=cell)
    p('Wniosek nie podlega opłacie skarbowej',size=9,italic=True,before=9,after=1)
    a = p('www.nowotarski.pl', WD_ALIGN_PARAGRAPH.RIGHT, size=10, italic=True, after=0)
    border=OxmlElement('w:pBdr');top=OxmlElement('w:top')
    for k,v in [('val','single'),('sz','4'),('color','808080')]:top.set(qn('w:'+k),v)
    border.append(top);a._p.get_or_add_pPr().append(border)
    p('(*) odpowiednie podkreślić',size=9,italic=True)
    cel=Path(cel);cel.parent.mkdir(parents=True,exist_ok=True);d.save(cel)
    return cel


if __name__=='__main__':
    print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'egib_zmiany.docx'))
