"""Buduje jednostronicowy Formularz P dla Starostwa Powiatowego w Nowym Targu."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent


def zbuduj(cel):
    d = Document(); s = d.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin = s.bottom_margin = Cm(.55); s.left_margin = s.right_margin = Cm(.65)
    s.header_distance = s.footer_distance = Cm(.25)
    normal = d.styles['Normal']; normal.font.name = 'Arial'; normal.font.size = Pt(7.5)
    normal.font.color.rgb = RGBColor(0, 0, 0); normal.paragraph_format.space_after = Pt(0); normal.paragraph_format.line_spacing = 1.0
    d.core_properties.title = 'Wniosek o udostępnienie materiałów powiatowego zasobu geodezyjnego i kartograficznego — Formularz P'
    d.core_properties.author = 'Dokumenty FILAR'

    def shade(cell, color='D9D9D9'):
        pr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), color); pr.append(shd)
    def margins(cell, n='35'):
        mar=OxmlElement('w:tcMar')
        for side in ('top','bottom','start','end'):
            el=OxmlElement('w:'+side);el.set(qn('w:w'),n);el.set(qn('w:type'),'dxa');mar.append(el)
        cell._tc.get_or_add_tcPr().append(mar)
    def setup(t):
        t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
        pr=t._tbl.tblPr;b=OxmlElement('w:tblBorders')
        for side in ('top','left','bottom','right','insideH','insideV'):
            e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'555555');b.append(e)
        pr.append(b)
        for row in t.rows:
            for c in row.cells:c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER;margins(c)
        return t
    def text(cell, val, size=7.5, bold=False, italic=False, align=None):
        p=cell.paragraphs[0] if not cell.paragraphs[0].text and len(cell.paragraphs)==1 else cell.add_paragraph()
        p.alignment=align;p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1.0
        r=p.add_run(val);r.font.name='Arial';r.font.size=Pt(size);r.bold=bold or None;r.italic=italic or None
        return p
    def label(cell, val):
        shade(cell);p=cell.paragraphs[0];p.paragraph_format.space_after=Pt(0)
        r=p.add_run(val);r.font.name='Arial';r.font.size=Pt(7);r.bold=True
    def field(cell, caption, var, size=7.5):
        label(cell,caption);text(cell,'{{ '+var+' }}',size)
    def section(title):
        t=setup(d.add_table(rows=1,cols=1));c=t.cell(0,0);shade(c,'BFBFBF')
        p=c.paragraphs[0];p.paragraph_format.space_after=Pt(0);r=p.add_run(title);r.bold=True;r.font.name='Arial';r.font.size=Pt(7.6)
    def choice(cell, group, key, caption, cl=''):
        style=f'P_{group}_{key}'
        if style not in d.styles:d.styles.add_style(style,WD_STYLE_TYPE.CHARACTER)
        p=cell.add_paragraph();p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=.9
        r=p.add_run('☐');r.style=style;r.font.name='Arial Unicode MS';r.font.size=Pt(7)
        p.paragraph_format.space_after=Pt(.7)
        r=p.add_run(' '+caption+(f'  CL {cl}' if cl else ''));r.font.name='Arial';r.font.size=Pt(7.0)

    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(1)
    r=p.add_run('WNIOSEK O UDOSTĘPNIENIE MATERIAŁÓW POWIATOWEGO ZASOBU GEODEZYJNEGO I KARTOGRAFICZNEGO');r.bold=True;r.font.name='Arial';r.font.size=Pt(9)
    t=setup(d.add_table(rows=2,cols=3));
    for row in t.rows:
        row.cells[0].width=Cm(10.5);row.cells[1].width=Cm(6.6);row.cells[2].width=Cm(2.6)
    label(t.cell(0,0),'1. Imię i nazwisko / nazwa oraz adres wnioskodawcy');label(t.cell(0,1),'2. Data');label(t.cell(0,2),'Formularz P')
    text(t.cell(1,0),'{{ wnioskodawca }}',8.2);text(t.cell(1,1),'Nowy Targ, dnia {{ data }}',8.2);text(t.cell(1,2),'P',12,True,align=WD_ALIGN_PARAGRAPH.CENTER)
    t=setup(d.add_table(rows=2,cols=2));t.columns[0].width=Cm(9.5);t.columns[1].width=Cm(10.2)
    label(t.cell(0,0),'3. Adresat wniosku');label(t.cell(0,1),'4. Dane kontaktowe wnioskodawcy')
    text(t.cell(1,0),'Starostwo Powiatowe w Nowym Targu, Wydział Geodezji, Katastru i Kartografii, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ',7.2)
    text(t.cell(1,1),'Telefon: {{ telefon }}    E-mail / adres do doręczeń: {{ kontakt }}',7.2)
    t=setup(d.add_table(rows=2,cols=2));t.columns[0].width=Cm(9.5);t.columns[1].width=Cm(10.2)
    label(t.cell(0,0),'5. Oznaczenie wniosku nadane przez wnioskodawcę (opcjonalnie)');label(t.cell(0,1),'6. Oznaczenie kancelaryjne (wypełnia urząd)')
    text(t.cell(1,0),'{{ oznaczenie }}',7.5);text(t.cell(1,1),'GK.6642.1. …………… .2026',8.5,True,align=WD_ALIGN_PARAGRAPH.CENTER)
    section('7. Określenie materiałów będących przedmiotem wniosku')
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(9.8);t.columns[1].width=Cm(9.9)
    left=[('mapa','Mapa zasadnicza lub mapa ewidencji gruntów i budynków'),('egib','Baza danych EGiB'),('gesut','Baza danych GESUT')]
    right=[('bdot500','Baza danych BDOT500'),('raporty','Raporty tworzone na podstawie bazy EGiB'),('inne','Inne materiały')]
    for cell,items in zip(t.rows[0].cells,(left,right)):
        for key,caption in items:choice(cell,'MATERIAL',key,caption)
    t=setup(d.add_table(rows=1,cols=1));field(t.cell(0,0),'Doprecyzowanie materiałów / zakres zamówienia','materialy_opis')
    section('8. Cel pobrania materiałów (zaznacz jeden właściwy)')
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(10.1);t.columns[1].width=Cm(9.6)
    for key,caption,cl in [('wlasne','Na potrzeby własne, niezwiązane z działalnością gospodarczą; bez prawa publikacji w Internecie','1.0'),('publiczne','Wykonanie zadań publicznych','1.0'),('dowolne','Dla dowolnych potrzeb','2.0'),('operator','Kolejne udostępnienie danych o sieci podmiotowi władającemu siecią','0.1')]:choice(t.cell(0,0),'CEL',key,caption,cl)
    for key,caption in [('edukacja','Cele edukacyjne — jednostka oświatowa, uczelnia lub podmiot pożytku publicznego'),('nauka','Prowadzenie badań naukowych lub prac rozwojowych'),('bezpieczenstwo','Ustawowe zadania służb specjalnych w zakresie bezpieczeństwa państwa'),('obronnosc','Zadania w zakresie obronności państwa — Minister Obrony Narodowej'),('operator_pierwszy','Pierwsze udostępnienie danych o sieci podmiotowi władającemu siecią')]:choice(t.cell(0,1),'CEL',key,caption)
    section('9. Dane identyfikujące obszar / osobę do kontaktu')
    t=setup(d.add_table(rows=2,cols=2));t.columns[0].width=Cm(10);t.columns[1].width=Cm(9.7)
    field(t.cell(0,0),'Położenie materiałów (województwo, powiat, gmina, miejscowość, ulica)','teren');field(t.cell(0,1),'Numery działek ewidencyjnych','dzialki')
    field(t.cell(1,0),'Obręb ewidencyjny','obreb');field(t.cell(1,1),'Osoba do kontaktu / telefon / e-mail','kontakt_osoba')
    section('10. Sposób udostępnienia materiałów')
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(9.8);t.columns[1].width=Cm(9.9)
    for key,caption in [('osobiscie','Odbiór osobisty w siedzibie organu'),('adres_naglowek','Wysyłka na adres z nagłówka'),('adres_inny','Wysyłka pod inny adres')]:choice(t.cell(0,0),'SPOSOB',key,caption)
    for key,caption in [('ftp','Usługa sieciowa — serwer FTP'),('email','Usługa sieciowa — wskazany adres e-mail'),('nosnik','Nośnik dostarczony przez wnioskodawcę')]:choice(t.cell(0,1),'SPOSOB',key,caption)
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(12);t.columns[1].width=Cm(7.7)
    field(t.cell(0,0),'Inny adres / e-mail / dane FTP','adres_inny');field(t.cell(0,1),'Dane nośnika','nosnik')
    section('11. Dodatkowe wyjaśnienia i uwagi wnioskodawcy')
    t=setup(d.add_table(rows=1,cols=1));text(t.cell(0,0),'{{ uwagi }}',7.5)
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(10);t.columns[1].width=Cm(9.7)
    label(t.cell(0,0),'12. Imię i nazwisko oraz czytelny podpis wnioskodawcy');text(t.cell(0,0),'{{ wnioskodawca }}\n\n................................................................................',7.5)
    text(t.cell(0,1),'Klauzula informacyjna RODO: Administratorem danych jest Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ. Pełna informacja: nowotarski.pl/polityka-prywatnosci/dokumenty/polityka-prywatnosci-812.html',6.2)
    p=d.add_paragraph();p.paragraph_format.space_before=Pt(1);p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    r=p.add_run('Wniosek sporządzono na podstawie wzoru Formularza P — Dz.U. 2026 poz. 1068. W razie potrzeby urząd może wymagać formularza uszczegóławiającego P1–P6.');r.font.name='Arial';r.font.size=Pt(4.8);r.italic=True
    Path(cel).parent.mkdir(parents=True,exist_ok=True);d.save(cel);return Path(cel)

if __name__=='__main__':print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'formularz_p.docx'))
