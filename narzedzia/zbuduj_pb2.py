"""Odtwarza dwustronicowy formularz PB-2 ze zdjęć użytkownika."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent.parent

def zbuduj(cel):
 d=Document();s=d.sections[0];s.page_width,s.page_height=Cm(21),Cm(29.7);s.top_margin=Cm(1.25);s.bottom_margin=Cm(1.2);s.left_margin=Cm(1.55);s.right_margin=Cm(1.55)
 normal=d.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(9);normal.font.color.rgb=RGBColor(0,0,0);normal.paragraph_format.space_after=Pt(2);normal.paragraph_format.line_spacing=1.0
 d.core_properties.title='Zgłoszenie budowy lub wykonywania innych robót budowlanych (PB-2)';d.core_properties.author='Dokumenty FILAR'
 def p(txt='',size=None,bold=False,align=None,before=0,after=2,italic=False):
  a=d.add_paragraph();a.alignment=align;a.paragraph_format.space_before=Pt(before);a.paragraph_format.space_after=Pt(after);r=a.add_run(txt);r.bold=bold or None;r.italic=italic or None
  if size:r.font.size=Pt(size)
  return a
 def shade(cell,fill='D9D9D9'):
  pr=cell._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),fill);pr.append(sh)
 def section(title):
  t=d.add_table(rows=1,cols=1);c=t.cell(0,0);shade(c);r=c.paragraphs[0].add_run(title);r.bold=True;r.font.size=Pt(10)
 def field(label,key, value='{{ pusty }}'):
  a=d.add_paragraph();a.paragraph_format.space_after=Pt(1);a.add_run(label+'  ');r=a.add_run(value);r.underline=True
 def fields(rows):
  t=d.add_table(rows=0,cols=2);t.autofit=False;t.columns[0].width=Cm(8.7);t.columns[1].width=Cm(8.7)
  for i in range(0,len(rows),2):
   cells=t.add_row().cells
   for j in range(2):
    if i+j>=len(rows):continue
    label,key=rows[i+j];a=cells[j].paragraphs[0];a.paragraph_format.space_after=Pt(1);a.add_run(label+' ');r=a.add_run('{{ '+key+' }}');r.underline=True
  for row in t.rows:
   for c in row.cells:
    pr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
    for side in ('top','left','bottom','right','insideH','insideV'):
     x=OxmlElement('w:'+side);x.set(qn('w:val'),'nil');b.append(x)
    pr.append(b)
 p('ZGŁOSZENIE',16,True,WD_ALIGN_PARAGRAPH.CENTER,after=0)
 p('budowy lub wykonywania innych robót budowlanych',13,True,WD_ALIGN_PARAGRAPH.CENTER,after=0)
 p('(PB-2)',12,True,WD_ALIGN_PARAGRAPH.CENTER,after=5)
 t=d.add_table(rows=1,cols=1);shade(t.cell(0,0),'E6E6E6');a=t.cell(0,0).paragraphs[0];a.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=a.add_run('PB-2 nie dotyczy budowy i przebudowy budynku mieszkalnego jednorodzinnego.');r.bold=True
 p('Podstawa prawna: art. 30 ust. 2 w zw. z ust. 4d ustawy z dnia 7 lipca 1994 r. – Prawo budowlane (Dz. U. z 2025 r. poz. 418, 1080, 1535, 1673 i 1847).',after=5)
 section('1. ORGAN ADMINISTRACJI ARCHITEKTONICZNO-BUDOWLANEJ');p('Nazwa: Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ',after=4)
 section('2.1. DANE INWESTORA¹)');fields([('Imię i nazwisko lub nazwa:','inwestor.imie_nazwisko'),('Kraj:','inwestor.kraj'),('Województwo:','inwestor.wojewodztwo'),('Powiat:','inwestor.powiat'),('Gmina:','inwestor.gmina'),('Ulica:','inwestor.ulica'),('Nr domu:','inwestor.nr_domu'),('Nr lokalu:','inwestor.nr_lokalu'),('Miejscowość:','inwestor.miejscowosc'),('Kod pocztowy:','inwestor.kod_pocztowy'),('E-mail (nieobowiązkowo):','email'),('Nr tel. (nieobowiązkowo):','telefon')])
 section('2.2. DANE INWESTORA (DO KORESPONDENCJI)¹)');p('Wypełnia się, jeżeli adres do korespondencji inwestora jest inny niż wskazany w pkt 2.1.',italic=True,after=2)
 fields([(lab,'korespondencja.'+key) for lab,key in [('Kraj:','kraj'),('Województwo:','wojewodztwo'),('Powiat:','powiat'),('Gmina:','gmina'),('Ulica:','ulica'),('Nr domu:','nr_domu'),('Nr lokalu:','nr_lokalu'),('Miejscowość:','miejscowosc'),('Kod pocztowy:','kod_pocztowy'),('Adres do doręczeń elektronicznych²):','adres_elektroniczny'),('E-mail (nieobowiązkowo):','email'),('Nr tel. (nieobowiązkowo):','telefon')]])
 section('3. DANE PEŁNOMOCNIKA / PEŁNOMOCNIKA DO DORĘCZEŃ¹)');p('Wypełnia się, jeżeli inwestor działa przez pełnomocnika.',italic=True,after=2)
 a=p('',after=2)
 for kod,tekst in [('pelnomocnik','☐ pełnomocnik'),('do_doreczen','     ☐ pełnomocnik do doręczeń')]:
  styl='PB2_TYP_'+kod
  if styl not in d.styles:d.styles.add_style(styl,WD_STYLE_TYPE.CHARACTER)
  r=a.add_run(tekst);r.style=styl
 p('')
 # Fotografia pierwszej strony kończy się bezpośrednio po wyborze rodzaju pełnomocnika.
 d.add_page_break()
 fields([('Imię i nazwisko:','proxy_nazwa'),('Kraj:','proxy.kraj'),('Województwo:','proxy.wojewodztwo'),('Powiat:','proxy.powiat'),('Gmina:','proxy.gmina'),('Ulica:','proxy.ulica'),('Nr domu:','proxy.nr_domu'),('Nr lokalu:','proxy.nr_lokalu'),('Miejscowość:','proxy.miejscowosc'),('Kod pocztowy:','proxy.kod_pocztowy'),('Adres do doręczeń elektronicznych²):','proxy.adres_elektroniczny'),('E-mail (nieobowiązkowo):','proxy.email'),('Nr tel. (nieobowiązkowo):','proxy.telefon')])
 section('4. INFORMACJE O ROBOTACH BUDOWLANYCH');p('Rodzaj, zakres i sposób wykonywania:');p('{{ roboty }}',after=5)
 p('Planowany termin rozpoczęcia³): {{ termin }}',after=5)
 section('5. DANE NIERUCHOMOŚCI (MIEJSCE WYKONYWANIA ROBÓT BUDOWLANYCH)¹)');fields([('Województwo:','nieruchomosc.wojewodztwo'),('Powiat:','nieruchomosc.powiat'),('Gmina:','nieruchomosc.gmina'),('Ulica:','nieruchomosc.ulica'),('Nr domu:','nieruchomosc.nr_domu'),('Miejscowość:','nieruchomosc.miejscowosc'),('Kod pocztowy:','nieruchomosc.kod_pocztowy'),('Identyfikator działki ewidencyjnej⁴):','nieruchomosc.identyfikator_dzialki')])
 section('6. ZAŁĄCZNIKI')
 for k,txt in [('OSWIADCZENIE','Oświadczenie o posiadanym prawie do dysponowania nieruchomością na cele budowlane.'),('PELNOMOCNICTWO','Pełnomocnictwo do reprezentowania inwestora (opłacone zgodnie z ustawą z dnia 16 listopada 2006 r. o opłacie skarbowej (Dz. U. z 2025 r. poz. 1154, 1795 i 1847)) – jeżeli inwestor działa przez pełnomocnika'),('OPLATA','Potwierdzenie uiszczenia opłaty skarbowej – jeżeli obowiązek uiszczenia takiej opłaty wynika z ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej.'),('INNE','Inne (wymagane przepisami prawa):')]:
  a=p('☐ '+txt,after=1)
  styl='PB2_ZAL_'+k
  if styl not in d.styles:d.styles.add_style(styl,WD_STYLE_TYPE.CHARACTER)
  a.runs[0].style=styl
 section('7. PODPIS INWESTORA (PEŁNOMOCNIKA) I DATA PODPISU');p('Podpis powinien być czytelny. Podpis i datę podpisu umieszcza się w przypadku dokonywania zgłoszenia w postaci papierowej.',italic=True);p('........................................................................................................................................',before=5,after=5)
 p('¹) W przypadku większej liczby inwestorów, pełnomocników lub nieruchomości dane kolejnych inwestorów, pełnomocników lub nieruchomości dodaje się w formularzu albo zamieszcza na osobnych stronach i dołącza do formularza.',size=7.5)
 p('²) W przypadku określonym w art. 147 ust. 1 ustawy z dnia 18 listopada 2020 r. o doręczeniach elektronicznych (Dz. U. z 2026 r. poz. 3) w razie braku adresu do doręczeń elektronicznych wskazuje się adres skrytki ePUAP. Możliwość doręczania korespondencji na skrytkę ePUAP obowiązuje do dnia określonego w tym przepisie.',size=7.5)
 p('³) W przypadku zgłoszenia budowy tymczasowego obiektu budowlanego w polu „Planowany termin rozpoczęcia” należy wskazać również planowany termin rozbiórki lub przeniesienia w inne miejsce tego obiektu.',size=7.5)
 p('⁴) W przypadku formularza w postaci papierowej zamiast identyfikatora działki ewidencyjnej można wskazać jednostkę ewidencyjną, obręb ewidencyjny i numer działki ewidencyjnej oraz arkusz mapy, jeżeli występuje.',size=7.5)
 Path(cel).parent.mkdir(parents=True,exist_ok=True);d.save(cel);return Path(cel)
if __name__=='__main__':print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'pb2_zgloszenie.docx'))
