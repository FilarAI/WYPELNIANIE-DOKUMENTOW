"""Odtwarza dwustronicowy formularz PB-2a na podstawie zdjęć użytkownika."""
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
 d=Document();s=d.sections[0];s.page_width,s.page_height=Cm(21),Cm(29.7);s.top_margin=Cm(1.2);s.bottom_margin=Cm(1.15);s.left_margin=Cm(1.55);s.right_margin=Cm(1.55)
 n=d.styles['Normal'];n.font.name='Arial';n.font.size=Pt(9.3);n.font.color.rgb=RGBColor(0,0,0);n.paragraph_format.space_after=Pt(1);n.paragraph_format.line_spacing=1.0
 d.core_properties.title='Zgłoszenie budowy lub przebudowy budynku mieszkalnego jednorodzinnego PB-2a';d.core_properties.author='Dokumenty FILAR'
 def p(txt='',size=None,bold=False,align=None,before=0,after=1,italic=False):
  a=d.add_paragraph();a.alignment=align;a.paragraph_format.space_before=Pt(before);a.paragraph_format.space_after=Pt(after);r=a.add_run(txt);r.bold=bold or None;r.italic=italic or None
  if size:r.font.size=Pt(size)
  return a
 def sec(txt):
  a=p(txt,11,True,before=3,after=1);a.paragraph_format.keep_with_next=True
 def field(label,key):
  a=p('',after=0);a.paragraph_format.keep_together=True;a.add_run(label+' ');r=a.add_run('{{ '+key+' }}');r.underline=True
 def box(label,key):
  a=p('☐ '+label,after=0);styl='PB2A_'+key
  if styl not in d.styles:d.styles.add_style(styl,WD_STYLE_TYPE.CHARACTER)
  a.runs[0].style=styl
 p('ZGŁOSZENIE',17,True,WD_ALIGN_PARAGRAPH.CENTER,after=0)
 p('budowy lub przebudowy budynku mieszkalnego jednorodzinnego',13.3,True,WD_ALIGN_PARAGRAPH.CENTER,after=0)
 p('(PB-2a)',12,True,WD_ALIGN_PARAGRAPH.CENTER,after=4)
 p('Podstawa prawna: art. 30 ust. 2 w zw. z ust. 4d ustawy z dnia 7 lipca 1994 r. – Prawo budowlane (Dz. U. z 2025 r. poz. 418, 1080, 1535, 1673 i 1847).',after=4)
 sec('1. ORGAN ADMINISTRACJI ARCHITEKTONICZNO-BUDOWLANEJ');p('Nazwa:   Starosta Nowotarski, ul. Bolesława Wstydliwego 14, 34-400 Nowy Targ',after=3)
 sec('2.1. DANE INWESTORA¹)')
 for label,key in [('Imię i nazwisko lub nazwa:','inwestor.imie_nazwisko'),('Kraj:','inwestor.kraj'),('Województwo:','inwestor.wojewodztwo'),('Powiat:','inwestor.powiat'),('Gmina:','inwestor.gmina'),('Ulica:','inwestor.ulica'),('Nr domu:','inwestor.nr_domu'),('Nr lokalu:','inwestor.nr_lokalu'),('Miejscowość:','inwestor.miejscowosc'),('Kod pocztowy:','inwestor.kod_pocztowy'),('E-mail (nieobowiązkowo):','email'),('Nr tel. (nieobowiązkowo):','telefon')]:field(label,key)
 sec('2.2. DANE INWESTORA (DO KORESPONDENCJI)¹)');p('Wypełnia się, jeżeli adres do korespondencji inwestora jest inny niż wskazany w pkt 2.1.',8.5,italic=True)
 for label,key in [('Kraj:','kraj'),('Województwo:','wojewodztwo'),('Powiat:','powiat'),('Gmina:','gmina'),('Ulica:','ulica'),('Nr domu:','nr_domu'),('Nr lokalu:','nr_lokalu'),('Miejscowość:','miejscowosc'),('Kod pocztowy:','kod_pocztowy'),('Adres do doręczeń elektronicznych²):','adres_elektroniczny'),('E-mail (nieobowiązkowo):','email'),('Nr tel. (nieobowiązkowo):','telefon')]:field(label,'korespondencja.'+key)
 sec('3. DANE PEŁNOMOCNIKA / PEŁNOMOCNIKA DO DORĘCZEŃ¹)');p('Wypełnia się, jeżeli inwestor działa przez pełnomocnika.',8.5,italic=True)
 a=p('',after=0)
 for key,label in [('pelnomocnik','☐ pełnomocnik'),('do_doreczen','     ☐ pełnomocnik do doręczeń')]:
  st='PB2A_TYP_'+key
  if st not in d.styles:d.styles.add_style(st,WD_STYLE_TYPE.CHARACTER)
  r=a.add_run(label);r.style=st
 for label,key in [('Imię i nazwisko:','proxy_nazwa'),('Kraj:','proxy.kraj'),('Województwo:','proxy.wojewodztwo'),('Powiat:','proxy.powiat'),('Gmina:','proxy.gmina'),('Ulica:','proxy.ulica')]:field(label,key)
 d.add_page_break()
 for label,key in [('Nr domu:','proxy.nr_domu'),('Nr lokalu:','proxy.nr_lokalu'),('Miejscowość:','proxy.miejscowosc'),('Kod pocztowy:','proxy.kod_pocztowy'),('Adres do doręczeń elektronicznych²):','proxy.adres_elektroniczny'),('E-mail (nieobowiązkowo):','proxy.email'),('Nr tel. (nieobowiązkowo):','proxy.telefon')]:field(label,key)
 sec('4. RODZAJ ZAMIERZENIA BUDOWLANEGO');p('Należy wskazać właściwe. Jeżeli zamierzenie obejmuje kilka rodzajów robót budowlanych, należy wskazać wszystkie właściwe.',8.5)
 for k,t in [('budowa','Budowa nowego budynku/nowych budynków.'),('rozbudowa','Rozbudowa budynku/budynków.'),('przebudowa','Przebudowa budynku/budynków.'),('nadbudowa','Nadbudowa budynku/budynków.'),('odbudowa','Odbudowa budynku/budynków.')]:box(t,'RODZAJ_'+k)
 sec('5. PLANOWANY TERMIN ROZPOCZĘCIA ROBÓT BUDOWLANYCH');field('','termin')
 sec('6. DANE NIERUCHOMOŚCI (MIEJSCE WYKONYWANIA ROBÓT BUDOWLANYCH)¹)')
 for label,key in [('Województwo:','wojewodztwo'),('Powiat:','powiat'),('Gmina:','gmina'),('Ulica:','ulica'),('Nr domu:','nr_domu'),('Miejscowość:','miejscowosc'),('Kod pocztowy:','kod_pocztowy'),('Identyfikator działki ewidencyjnej³):','identyfikator_dzialki')]:field(label,'nieruchomosc.'+key)
 sec('7. ZAŁĄCZNIKI')
 zal=[('oswiadczenie','Oświadczenie o posiadanym prawie do dysponowania nieruchomością na cele budowlane.'),('pelnomocnictwo','Pełnomocnictwo do reprezentowania inwestora (opłacone zgodnie z ustawą z dnia 16 listopada 2006 r. o opłacie skarbowej (Dz. U. z 2025 r. poz. 1154, 1795 i 1847)) – jeżeli inwestor działa przez pełnomocnika.'),('oplata','Potwierdzenie uiszczenia opłaty skarbowej – jeżeli obowiązek uiszczenia takiej opłaty wynika z ustawy z dnia 16 listopada 2006 r. o opłacie skarbowej.'),('projekt','Projekt zagospodarowania działki lub terenu oraz projekt architektoniczno-budowlany (w postaci papierowej w 3 egzemplarzach albo w postaci elektronicznej).'),('warunki','Decyzja o warunkach zabudowy i zagospodarowania terenu – jeżeli jest ona wymagana zgodnie z przepisami o planowaniu i zagospodarowaniu przestrzennym⁴).'),('inne','Inne (wymagane przepisami prawa):')]
 for k,t in zal:box(t,'ZAL_'+k)
 sec('8. PODPIS INWESTORA (PEŁNOMOCNIKA) I DATA PODPISU');p('Podpis powinien być czytelny. Podpis i datę podpisu umieszcza się w przypadku dokonywania zgłoszenia w postaci papierowej.',8.5);p('........................................................................................................................................',before=3,after=3)
 p('¹) W przypadku większej liczby inwestorów, pełnomocników lub nieruchomości dane kolejnych inwestorów, pełnomocników lub nieruchomości dodaje się w formularzu albo zamieszcza na osobnych stronach i dołącza do formularza.',7.3)
 p('²) W przypadku określonym w art. 147 ust. 1 ustawy z dnia 18 listopada 2020 r. o doręczeniach elektronicznych (Dz. U. z 2026 r. poz. 3) w razie braku adresu do doręczeń elektronicznych wskazuje się adres skrytki ePUAP. Możliwość doręczania korespondencji na skrzynkę ePUAP obowiązuje do dnia określonego w tym przepisie.',7.3)
 p('³) W przypadku formularza w postaci papierowej zamiast identyfikatora działki ewidencyjnej można wskazać jednostkę ewidencyjną, obręb ewidencyjny i numer działki ewidencyjnej oraz arkusz mapy, jeżeli występuje.',7.3)
 p('⁴) Zamiast oryginału można dołączyć kopię dokumentu.',7.3)
 Path(cel).parent.mkdir(parents=True,exist_ok=True);d.save(cel);return Path(cel)
if __name__=='__main__':print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'pb2a_zgloszenie.docx'))
