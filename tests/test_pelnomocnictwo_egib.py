import io,zipfile
import pytest
from docx import Document
from werkzeug.datastructures import MultiDict
from app.main import app,_dane_z_formularza

BASE={'dokumenty':'pelnomocnictwo_egib','inw-0-imie_nazwisko':'Julia Testowa','inw-0-ulica':'Testowa','inw-0-nr_domu':'12','inw-0-kod_pocztowy':'34-400','inw-0-miejscowosc':'Nowy Targ','pel-egib-0-dowod':'ABC123456','pel-egib-0-organ':'Burmistrz Nowego Targu','pel-egib-0-pesel':'90010112345','pel-egib-pelnomocnik-dowod':'XYZ123456','pel-egib-pelnomocnik-organ':'Burmistrz Rabki-Zdroju','pel-egib-pelnomocnik-pesel':'80020212345','pel-egib-zakres':'samodzielnie'}

def test_generuje_pelnomocnictwo_egib_z_zakresem_i_podpisem():
 with app.test_client() as c:r=c.post('/generuj',data=BASE)
 assert r.status_code==200
 with zipfile.ZipFile(io.BytesIO(r.data)) as z:
  assert z.namelist()==['Pelnomocnictwo_EGiB_Testowa.docx'];d=Document(io.BytesIO(z.read(z.namelist()[0])))
 text='\n'.join(p.text for p in d.paragraphs)
 assert all(x in text for x in ['Julia Testowa','90010112345','ABC123456','Bartłomiej Filar','80020212345','☒','☐','złożeniem wniosku o wypis/wyrys'])
 assert '{{' not in text
 assert any(r.style.name=='PELEGIB_CHECK_samodzielnie' and r.text=='☒' for p in d.paragraphs for r in p.runs)
 assert any(r.style.name=='PELEGIB_CHECK_podpisany' and r.text=='☐' for p in d.paragraphs for r in p.runs)

@pytest.mark.parametrize('changes,expected',[
 ({'pel-egib-0-pesel':'123'},'11-cyfrowy PESEL'),
 ({'pel-egib-pelnomocnik-pesel':''},'PESEL pełnomocnika'),
 ({'pel-egib-zakres':'zly'},'wybierz właściwy zakres'),
 ({'pel-egib-0-dowod':''},'numer dowodu'),
])
def test_bledne_dane_i_brak_zakresu_blokuja(changes,expected):
 with app.test_client() as c:r=c.post('/generuj',data=BASE|changes)
 assert r.status_code==400 and expected in r.get_data(as_text=True)

def test_pozostale_dokumenty_nie_wymagaja_danych_dowodu():
 data=_dane_z_formularza(MultiDict({'dokumenty':'pelnomocnictwo','inw-0-imie_nazwisko':'Jan Testowy'}))
 assert 'pelnomocnictwo_egib' not in data
