"""Odtworzenie widocznej strony pełnomocnictwa EGiB ze zdjęcia."""
from pathlib import Path
import sys
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def zbuduj(cel):
 d=Document();s=d.sections[0];s.page_width=Cm(21);s.page_height=Cm(29.7);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.8);s.left_margin=Cm(2.3);s.right_margin=Cm(2.3)
 for n in ['Normal','Title']:
  st=d.styles[n];st.font.name='Times New Roman';st.font.size=Pt(12);st.font.color.rgb=RGBColor(0,0,0);st.paragraph_format.space_after=Pt(1);st.paragraph_format.line_spacing=1.0
 def p(t='',size=12,bold=False,italic=False,align=None,before=0,after=3):
  a=d.add_paragraph();a.alignment=align;a.paragraph_format.space_before=Pt(before);a.paragraph_format.space_after=Pt(after);r=a.add_run(t);r.font.name='Times New Roman';r.font.size=Pt(size);r.bold=bold or None;r.italic=italic or None;return a
 p('{{ miejsce_data }}',align=WD_ALIGN_PARAGRAPH.RIGHT,after=22)
 p('PEŁNOMOCNICTWO',size=17,bold=True,align=WD_ALIGN_PARAGRAPH.CENTER,after=27)
 p('Ja niżej podpisany/a {{ mocodawcy }}',after=16)
 p('ustanawiam pełnomocnika',after=9)
 p('{{ pelnomocnik }}',after=1)
 p('(imię, nazwisko osoby upoważnionej, stopień pokrewieństwa, jeżeli występuje)',size=10,italic=True,align=WD_ALIGN_PARAGRAPH.CENTER,after=11)
 p('zamieszkałego w {{ adres_pelnomocnika }}',after=0)
 p('(pełny adres zamieszkania)',size=10,italic=True,align=WD_ALIGN_PARAGRAPH.CENTER,after=10)
 p('legitymującego się dowodem osobistym numer {{ dowod_pelnomocnika }}',after=13)
 p('wydanym przez {{ organ_pelnomocnika }}',after=13)
 p('posiadającego numer PESEL {{ pesel_pelnomocnika }}',after=16)
 p('do załatwienia wszelkich formalności związanych ze (właściwe zaznaczyć):',after=6)
 for key,txt in [('samodzielnie','złożeniem wniosku o wypis/wyrys* z rejestru EGiB i odbiór dokumentu przez pełnomocnika'),('podpisany','złożeniem wniosku o wypis/wyrys* z rejestru EGiB wypełnionego i podpisanego przez właściciela/władającego nieruchomością i odbiór w/w dokumentu przez pełnomocnika')]:
  a=d.add_paragraph();a.paragraph_format.left_indent=Cm(.35);a.paragraph_format.first_line_indent=Cm(-.35);a.paragraph_format.space_before=Pt(5);a.paragraph_format.space_after=Pt(5)
  r=a.add_run('☐\u00a0\u00a0\u00a0');r.font.name='Arial Unicode MS';r.font.size=Pt(11);style=d.styles.add_style('PELEGIB_CHECK_'+key,WD_STYLE_TYPE.CHARACTER);r.style=style
  r=a.add_run(txt);r.font.name='Times New Roman';r.font.size=Pt(11)
  style=d.styles.add_style('PELEGIB_'+key,WD_STYLE_TYPE.CHARACTER);r.style=style
 p('* - niepotrzebne skreślić',size=10,after=17)
 p('{{ podpisy }}',align=WD_ALIGN_PARAGRAPH.RIGHT,after=0)
 p('(czytelny podpis osoby udzielającej pełnomocnictwa)',size=10,italic=True,align=WD_ALIGN_PARAGRAPH.RIGHT,after=0)
 cel=Path(cel);cel.parent.mkdir(parents=True,exist_ok=True);d.save(cel);return cel
if __name__=='__main__':print(zbuduj(sys.argv[1] if len(sys.argv)>1 else Path(__file__).parents[1]/'szablony/pelnomocnictwo_egib.docx'))
