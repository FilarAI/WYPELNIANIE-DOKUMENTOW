"""Odtwarza jednostronicowy druk BA-4 ze zdjęcia dostarczonego 19.11.2026."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent


def zbuduj(cel):
    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.top_margin, sec.bottom_margin = Cm(1.7), Cm(1.6)
    sec.left_margin, sec.right_margin = Cm(2), Cm(2)
    for name in ['Normal', 'Title']:
        st = d.styles[name]; st.font.name = 'Times New Roman'; st.font.color.rgb = RGBColor(0, 0, 0)
        st.font.size = Pt(11)
        st.paragraph_format.space_after = Pt(3)
        st.paragraph_format.line_spacing = 1.0
        for border in list(st.element.iter(qn('w:pBdr'))): border.getparent().remove(border)
    d.styles['Title'].font.size = Pt(13)
    d.core_properties.title = 'BA-4 Wniosek o wydanie dziennika budowy lub rozbiórki'
    d.core_properties.author = 'Dokumenty FILAR'

    def p(text='', align=None, before=0, after=3, size=None, bold=False, italic=False, style=None):
        a = d.add_paragraph(style=style)
        a.alignment = align
        a.paragraph_format.space_before = Pt(before); a.paragraph_format.space_after = Pt(after)
        r = a.add_run(text); r.font.name = 'Times New Roman'; r.bold = bold or None; r.italic = italic or None
        if size:r.font.size = Pt(size)
        return a

    def option(a, text, key):
        name = 'BA4_' + key
        if name not in d.styles:
            d.styles.add_style(name, WD_STYLE_TYPE.CHARACTER)
        r = a.add_run(text); r.style = name; r.font.name = 'Times New Roman'
        return r

    p('BA-4', WD_ALIGN_PARAGRAPH.RIGHT, after=12, size=16, bold=True)
    p('Nowy Targ, dnia: {{ data_wniosku }}', WD_ALIGN_PARAGRAPH.RIGHT, after=6)
    t=d.add_table(rows=1, cols=2);t.autofit=False
    t.columns[0].width=Cm(8);t.columns[1].width=Cm(9)
    for side in ['top','left','bottom','right','insideH','insideV']:
        borders=t._tbl.tblPr.find(qn('w:tblBorders'))
        if borders is None:borders=OxmlElement('w:tblBorders');t._tbl.tblPr.append(borders)
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'nil');borders.append(e)
    left,right=t.rows[0].cells
    def cellp(cell,text,first=False,caption=False,before=0,bold=False,italic=False,size=11):
        a=cell.paragraphs[0] if first else cell.add_paragraph()
        a.alignment=WD_ALIGN_PARAGRAPH.CENTER
        a.paragraph_format.space_before=Pt(before);a.paragraph_format.space_after=Pt(1)
        r=a.add_run(text);r.font.size=Pt(size);r.bold=bold or None;r.italic=italic or caption or None
        return a
    cellp(left,'{{ inwestorzy }}',True)
    cellp(left,'(Imię i nazwisko / nazwa Inwestora)',caption=True,size=9)
    cellp(left,'{{ adresy }}',before=13)
    cellp(left,'(adres zamieszkania / siedziby)',caption=True,size=9)
    cellp(right,'STAROSTA NOWOTARSKI',True,before=24,bold=True,italic=True,size=14)
    cellp(right,'34-400 Nowy Targ,',bold=True,size=13)
    cellp(right,'ul. Bolesława Wstydliwego 14',size=12)
    cellp(right,'Wydział Administracji',size=12)
    cellp(right,'Budowlano – Architektonicznej',size=12)

    p('W N I O S E K',WD_ALIGN_PARAGRAPH.CENTER,before=16,after=0,bold=True,italic=True,style='Title')
    a=p('O  WYDANIE  DZIENNIKA  ',WD_ALIGN_PARAGRAPH.CENTER,after=16,bold=True,italic=True,style='Title')
    for text,key in [('BUDOWY*','rodzaj_budowa'),(' /',''),('ROZBIÓRKI*','rodzaj_rozbiorka')]:
        r=option(a,text,key) if key else a.add_run(text);r.bold=True;r.italic=True
    a=p('W związku z zamiarem ',after=0)
    option(a,'rozpoczęcia robót budowlanych*','cel_rozpoczecie');a.add_run('/')
    option(a,'prowadzeniem robót budowlanych*','cel_kontynuacja')
    a=p('na podstawie ',after=6)
    option(a,'wydanego pozwolenia na ','prefiks_pozwolenie')
    option(a,'budowę*','podstawa_pozwolenie_budowa');a.add_run(' / ')
    option(a,'rozbiórkę*','podstawa_pozwolenie_rozbiorka');a.add_run(' / ')
    option(a,'przyjętego zgłoszenia*','podstawa_zgloszenie')
    p('{{ inwestycja }}',after=0)
    p('(podać rodzaj zamierzenia budowlanego, oraz miejsce lokalizacji inwestycji której decyzja/zgłoszenie dotyczy)',WD_ALIGN_PARAGRAPH.CENTER,after=8,size=8.5)
    p('przez {{ organ }}',after=0)
    p('(wymienić organ wydający pozwolenie na budowę)',WD_ALIGN_PARAGRAPH.CENTER,after=5,size=9)
    p('znak: {{ znak }}',after=6)
    p('z dnia: {{ data_pozwolenia }}',after=8)
    a=p('proszę o wydanie dziennika ',after=0,bold=True)
    option(a,'budowy ','rzeczownik_budowa').bold=True
    a.add_run('/');option(a,'pierwszego*','kolejnosc_pierwszy');a.add_run(', ')
    option(a,'kolejnego*','kolejnosc_kolejny');a.add_run(' – (podać nr')
    p('poprzedniego) {{ poprzedni_numer }} .',after=9)
    p('Jednocześnie - świadomy odpowiedzialności karnej, wynikającej z art. 233 Kodeksu karnego za poświadczenie nieprawdy – oświadczam, że:',after=7)
    a=p('* 1) Znane mi są przepisy art. 41 ust. 4 Prawa budowlanego dotyczące konieczności zawiadomienia o zamierzonym terminie rozpoczęcia robót budowlanych Powiatowego Inspektora Nadzoru Budowlanego w Nowym Targu oraz projektanta.',after=4)
    a.paragraph_format.left_indent=Cm(.2);a.paragraph_format.first_line_indent=Cm(-.2)
    a=p('* 2) Nie upłynęły 3 lata od dnia, w którym budowa została przerwana (odpowiedni wpis znajduje się w dzienniku budowy).',after=4)
    a.paragraph_format.left_indent=Cm(.2);a.paragraph_format.first_line_indent=Cm(-.2)
    a=p('* 3) Dziennik budowy który ',after=0)
    option(a,'posiadam*','posiadanie_posiadam');a.add_run(' / ')
    option(a,'posiadałem/am*','posiadanie_posiadalem');a.add_run(' / - został ')
    option(a,'w całości zapisany*','stan_zapisany');a.add_run('/')
    option(a,'zagubiony*','stan_zagubiony');a.add_run(' / ')
    option(a,'zniszczony*','stan_zniszczony');a.add_run(' /')
    p('{{ okolicznosci }}',after=0)
    p('(podać ewentualne okoliczności zagubienia lub zniszczenia)',WD_ALIGN_PARAGRAPH.CENTER,after=12,size=9)
    p('………………………………………………………………',WD_ALIGN_PARAGRAPH.RIGHT,after=0)
    p('(podpis inwestora lub osoby przez niego upoważnionej)',WD_ALIGN_PARAGRAPH.RIGHT,after=12,size=9,italic=True)
    p('Załączniki:',after=2,bold=True,italic=True,size=12)
    p('1.   Ostateczna decyzja o pozwoleniu na budowę, lub w przypadku zgłoszenia - opieczętowany projekt budowlany (do wglądu).',after=3)
    p('2.   Inne w zależności od potrzeb;',after=15)
    p('* niepotrzebne skreślić',size=9)
    cel=Path(cel);cel.parent.mkdir(parents=True,exist_ok=True);d.save(cel)
    return cel


if __name__=='__main__':
    print(zbuduj(sys.argv[1] if len(sys.argv)>1 else ROOT/'szablony'/'ba4_dziennik.docx'))
