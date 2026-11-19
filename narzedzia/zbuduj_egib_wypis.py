"""Buduje lokalny wariant formularza EGiB do wypisu/wyrysu ze zdjęcia."""
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
    s.top_margin = s.bottom_margin = Cm(.75); s.left_margin = s.right_margin = Cm(.8)
    normal = d.styles['Normal']; normal.font.name = 'Arial'; normal.font.size = Pt(7)
    normal.font.color.rgb = RGBColor(0, 0, 0); normal.paragraph_format.space_after = Pt(0); normal.paragraph_format.line_spacing = 0.95
    d.core_properties.title = 'Wniosek EGiB o wydanie wypisu lub wyrysu z operatu ewidencyjnego'
    d.core_properties.author = 'Dokumenty FILAR'

    def shade(cell, color='D9D9D9'):
        pr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:fill'), color); pr.append(shd)
    def borders(table):
        pr = table._tbl.tblPr; b = OxmlElement('w:tblBorders')
        for side in ('top','left','bottom','right','insideH','insideV'):
            e = OxmlElement('w:'+side); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'5'); e.set(qn('w:color'),'555555'); b.append(e)
        pr.append(b)
    def setup(t):
        t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False; borders(t)
        for row in t.rows:
            for c in row.cells:
                c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                mar = OxmlElement('w:tcMar')
                for side in ('top','bottom','start','end'):
                    el = OxmlElement('w:'+side); el.set(qn('w:w'),'45'); el.set(qn('w:type'),'dxa'); mar.append(el)
                c._tc.get_or_add_tcPr().append(mar)
        return t
    def p(cell, text='', bold=False, size=7, italic=False, align=None):
        a = cell.add_paragraph(); a.alignment = align; a.paragraph_format.space_after = Pt(0); a.paragraph_format.line_spacing = .95
        r = a.add_run(text); r.font.name='Arial'; r.font.size=Pt(size); r.bold=bold or None; r.italic=italic or None
        return a
    def label(cell, text):
        a = cell.paragraphs[0]; a.paragraph_format.space_after = Pt(1)
        r=a.add_run(text); r.font.name='Arial'; r.font.size=Pt(6.3); r.bold=True; shade(cell)
    def inputline(cell, caption, var, rows=1):
        label(cell, caption)
        a = p(cell, '{{ '+var+' }}' if rows==1 else '{{ '+var+' }}', size=8)
        a.paragraph_format.space_before = Pt(1); a.paragraph_format.space_after=Pt(1)
        if rows>1:
            for _ in range(rows-1): p(cell, '.........................................................................................................................', size=6)
    def section(title):
        t=setup(d.add_table(rows=1,cols=1)); c=t.cell(0,0); shade(c,'BFBFBF');
        a=c.paragraphs[0]; a.paragraph_format.space_after=Pt(0); r=a.add_run(title); r.bold=True; r.font.name='Arial'; r.font.size=Pt(7.1)
        return t
    def choice(cell, codestyle, code, caption):
        a=cell.add_paragraph(); a.paragraph_format.space_after=Pt(0); a.paragraph_format.line_spacing=.95
        style='EGIBW_'+codestyle+'_'+code.upper()
        if style not in d.styles: d.styles.add_style(style, WD_STYLE_TYPE.CHARACTER)
        r=a.add_run('☐ '); r.style=style; r.font.name='Arial Unicode MS'; r.font.size=Pt(8)
        rr=a.add_run(caption); rr.font.name='Arial'; rr.font.size=Pt(6.7)
        return a

    a=d.add_paragraph(); a.alignment=WD_ALIGN_PARAGRAPH.CENTER; a.paragraph_format.space_after=Pt(2)
    r=a.add_run('Wniosek o wydanie wypisu lub wyrysu z operatu ewidencyjnego'); r.bold=True; r.font.name='Arial'; r.font.size=Pt(10)
    t=setup(d.add_table(rows=2,cols=3)); widths=[Cm(8.6),Cm(8.7),Cm(2.0)]
    for row in t.rows:
        for i,c in enumerate(row.cells): c.width=widths[i]
    for c,txt in zip(t.rows[0].cells,['1. Imię i nazwisko / nazwa oraz adres wnioskodawcy','2. Data','Formularz EGiB']): label(c,txt)
    inputline(t.cell(1,0),'','wnioskodawca',3); inputline(t.cell(1,1),'Nowy Targ, dnia','data'); p(t.cell(1,2),'EGiB',True,10,align=WD_ALIGN_PARAGRAPH.CENTER)
    t=setup(d.add_table(rows=2,cols=2)); t.columns[0].width=Cm(8.6);t.columns[1].width=Cm(10.7)
    label(t.cell(0,0),'5. Dane kontaktowe wnioskodawcy (telefon / e-mail / adres do doręczeń elektronicznych)'); label(t.cell(0,1),'3. Adresat wniosku — organ prowadzący państwowy zasób geodezyjny i kartograficzny')
    inputline(t.cell(1,0),'','kontakt',2); p(t.cell(1,1),'Starostwo Powiatowe w Nowym Targu\nWydział Geodezji, Katastru i Kartografii\nul. Bolesława Wstydliwego 14, 34-400 Nowy Targ',size=7.5)
    t=setup(d.add_table(rows=2,cols=2));t.columns[0].width=Cm(8.6);t.columns[1].width=Cm(10.7)
    label(t.cell(0,0),'4. PESEL lub REGON wnioskodawcy'); label(t.cell(0,1),'6. Oznaczenie wniosku nadane przez wnioskodawcę*')
    inputline(t.cell(1,0),'','pesel_regon');inputline(t.cell(1,1),'','oznaczenie')
    t=setup(d.add_table(rows=2,cols=2));t.columns[0].width=Cm(8.6);t.columns[1].width=Cm(10.7)
    label(t.cell(0,0),'7. Oznaczenie kancelaryjne wniosku nadane przez adresata wniosku'); label(t.cell(0,1),'')
    p(t.cell(1,0),'GK.6621. ........................................ . 2026',True,9,align=WD_ALIGN_PARAGRAPH.CENTER);p(t.cell(1,1),'Pole wypełnia adresat wniosku',italic=True,align=WD_ALIGN_PARAGRAPH.CENTER)
    section('8. Przedmiot wniosku')
    t=setup(d.add_table(rows=1,cols=2));t.columns[0].width=Cm(9.6);t.columns[1].width=Cm(9.7)
    left=['wypis_grunty','wypis_grunty_wyrys','wyrys','uproszczony','bez_danych']; right=['kartoteka_budynkow','kartoteka_lokali','rejestr_budynkow','rejestr_lokali','wykaz_dzialek','wykaz_podmiotow']
    opisy={'wypis_grunty':'Wypis z rejestru gruntów','wypis_grunty_wyrys':'Wypis z rejestru gruntów oraz wyrys z mapy ewidencyjnej','wyrys':'Wyrys z mapy ewidencyjnej','uproszczony':'Uproszczony wypis z rejestru gruntów','bez_danych':'Wypis z rejestru gruntów bez danych osobowych','kartoteka_budynkow':'Wypis z kartoteki budynków','kartoteka_lokali':'Wypis z kartoteki lokali','rejestr_budynkow':'Wypis z rejestru budynków','rejestr_lokali':'Wypis z rejestru lokali','wykaz_dzialek':'Wypis z wykazu działek ewidencyjnych','wykaz_podmiotow':'Wypis z wykazu podmiotów'}
    for cell,items in zip(t.rows[0].cells,(left,right)):
        for code in items: choice(cell,'PRZEDMIOT',code,opisy[code])
    section('9. Dane identyfikujące nieruchomość, której dotyczy wniosek')
    t=setup(d.add_table(rows=3,cols=2));t.columns[0].width=Cm(9.6);t.columns[1].width=Cm(9.7)
    for c,cap,var in [(t.cell(0,0),'Powiat:','powiat'),(t.cell(0,1),'Nr jednostki rejestrowej:','jednostka'),(t.cell(1,0),'Gmina:','gmina'),(t.cell(1,1),'Obręb ewidencyjny:','obreb'),(t.cell(2,0),'Nr działek ewidencyjnych:','dzialki'),(t.cell(2,1),'Nr budynków / lokali / księgi wieczystej / adres nieruchomości:','adres_nieruchomosci')]: inputline(c,cap,var)
    section('10. Uzasadnienie wniosku o wypis zawierający dane podmiotów (art. 20 ust. 2 pkt 1 ustawy — Prawo geodezyjne i kartograficzne)')
    t=setup(d.add_table(rows=1,cols=1)); c=t.cell(0,0)
    uzasadnienia=[('wlasciciel','Wnioskodawca jest właścicielem lub władającym nieruchomością'),('zadania_publiczne','Wykonuje zadania publiczne związane z nieruchomością'),('operator_sieci','Jest operatorem sieci telekomunikacyjnej'),('operator_energetyczny','Jest operatorem systemu przesyłowego/dystrybucyjnego'),('interes_prawny','Ma interes prawny w dostępie do danych')]
    for code,caption in uzasadnienia: choice(c,'UZASADNIENIE',code,caption)
    a=c.add_paragraph();a.paragraph_format.space_after=Pt(0);r=a.add_run('Interes prawny — akt: {{ uzasadnienie_akt }}    okoliczności: {{ uzasadnienie_okolicznosci }}');r.font.name='Arial';r.font.size=Pt(6.5)
    section('11. Osoba wyznaczona do kontaktu ze strony wnioskodawcy')
    t=setup(d.add_table(rows=1,cols=3));
    for c,cap,var in zip(t.rows[0].cells,['Imię i nazwisko:','E-mail:','Telefon:'],['kontakt_osoba','email','telefon']):inputline(c,cap,var)
    section('12. Postać dokumentów i sposób ich udostępnienia')
    t=setup(d.add_table(rows=1,cols=2));
    for code,caption in [('papierowa','Postać papierowa'),('elektroniczna','Postać elektroniczna')]:choice(t.cell(0,0),'POSTAC',code,caption)
    for code,caption in [('osobiscie','Odbiór osobisty w siedzibie organu'),('wysylka_naglowek','Wysyłka pod adres z nagłówka'),('wysylka_inny','Wysyłka pod inny adres'),('inny','Inny sposób odbioru')]:choice(t.cell(0,1),'ODBIOR',code,caption)
    p(t.cell(0,1),'Inny adres: {{ inny_adres }}',size=6.5)
    section('13. Dodatkowe wyjaśnienia i uwagi wnioskodawcy')
    t=setup(d.add_table(rows=1,cols=1));p(t.cell(0,0),'{{ uwagi }}',size=7)
    section('14. Imię i nazwisko oraz podpis wnioskodawcy')
    a=d.add_paragraph();r=a.add_run('{{ wnioskodawca }}');r.font.name='Arial';r.font.size=Pt(8)
    a=d.add_paragraph();a.alignment=WD_ALIGN_PARAGRAPH.RIGHT;a.paragraph_format.space_before=Pt(6);r=a.add_run('...................................................................\n(czytelny podpis wnioskodawcy)');r.font.name='Arial';r.font.size=Pt(7)
    a=d.add_paragraph();r=a.add_run('Klauzula informacyjna administratora danych osobowych: Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ. Pełna informacja: www.nowotarski.pl/polityka-prywatnosci/dokumenty/polityka-prywatnosci-812.html');r.font.name='Arial';r.font.size=Pt(5.5)
    Path(cel).parent.mkdir(parents=True,exist_ok=True);d.save(cel);return Path(cel)

if __name__=='__main__': print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'egib_wypis_wyrys.docx'))
