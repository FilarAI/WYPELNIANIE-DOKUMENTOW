"""PB-2a: wybór rodzajów robót, termin, załączniki i walidacja."""
import io,zipfile
from docx import Document
import pytest
from app.main import app

BASE={"dokumenty":"pb2a","wybor_potwierdzony":"tak","inw-0-imie_nazwisko":"Krzysztof Testowy","inw-0-miejscowosc":"Kraków","inw-0-ulica":"ul. Przykładowa","inw-0-nr_domu":"12","inw-0-nr_lokalu":"4","inw-0-kod_pocztowy":"30-001","adres-miejscowosc":"Zakopane","adres-ulica":"ul. Słoneczna","adres-nr_domu":"8","adres-kod_pocztowy":"34-500","adres-nr_dzialki":"245/7","adres-identyfikator_dzialki":"121701_1.0005.245/7","pb2a-rodzaje":["rozbudowa","przebudowa"],"pb2a-termin":"15.03.2027"}

def dokument(form):
    with app.test_client() as c:r=c.post('/generuj',data=form)
    assert r.status_code==200,r.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        assert z.namelist()==['PB-2a_Krzysztof_Testowy.docx']
        return Document(io.BytesIO(z.read(z.namelist()[0])))

def przebiegi(d):
    for p in d.paragraphs: yield from p.runs
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs: yield from p.runs

def test_pb2a_tresc_i_zaznaczone_rodzaje():
    d=dokument(BASE|{"pb2a-0-zal-projekt":"tak","pb2a-0-zal-warunki":"tak","pb2a-0-zal-inne":"tak","pb2a-0-zal-opis":"Mapa do celów projektowych"})
    rs=list(przebiegi(d));txt='\n'.join(r.text for r in rs)
    for s in ['PB-2a','Krzysztof Testowy','15.03.2027','121701_1.0005.245/7','Mapa do celów projektowych','Dz. U. z 2026 r. poz. 3','Zamiast oryginału można dołączyć kopię dokumentu']:
        assert s in txt
    assert '{{' not in txt
    assert next(r for r in rs if r.style.name=='PB2A_RODZAJ_rozbudowa').text.startswith('☒')
    assert next(r for r in rs if r.style.name=='PB2A_RODZAJ_przebudowa').text.startswith('☒')
    assert next(r for r in rs if r.style.name=='PB2A_RODZAJ_budowa').text.startswith('☐')
    assert next(r for r in rs if r.style.name=='PB2A_ZAL_projekt').text.startswith('☒')
    assert next(r for r in rs if r.style.name=='PB2A_ZAL_oswiadczenie').text.startswith('☐')

def test_pb2a_pelnomocnik_i_kontakt():
    d=dokument(BASE|{"pb2a-0-typ_pelnomocnika":"do_doreczen","pb2a-0-proxy-imie_nazwisko":"Anna Przykładowa","pb2a-0-proxy-kraj":"Polska","pb2a-0-proxy-miejscowosc":"Nowy Targ","pb2a-0-email":"kontakt@example.invalid"})
    rs=list(przebiegi(d));assert 'Anna Przykładowa' in '\n'.join(r.text for r in rs)
    assert next(r for r in rs if r.style.name=='PB2A_TYP_do_doreczen').text.count('☒')==1
    assert next(r for r in rs if r.style.name=='PB2A_TYP_pelnomocnik').text.count('☐')==1

@pytest.mark.parametrize('zmiany,blad',[( {'pb2a-rodzaje':[]},'co najmniej jeden rodzaj'),({'pb2a-rodzaje':['rozbudowa','rozbudowa']},'poprawne rodzaje'),({'pb2a-rodzaje':['inne']},'poprawne rodzaje'),({'pb2a-termin':''},'podaj planowany termin'),({'pb2a-termin':'31.02.2027'},'poprawną datą'),({'pb2a-termin':'2027-03-15'},'format DD.MM.RRRR'),({'pb2a-0-typ_pelnomocnika':'pelnomocnik'},'podaj imię i nazwisko')])
def test_bledne_dane_pb2a_nie_przechodza(zmiany,blad):
    with app.test_client() as c:r=c.post('/generuj',data=BASE|zmiany)
    assert r.status_code==400 and blad in r.get_data(as_text=True)
