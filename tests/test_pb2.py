"""PB-2: formularz dwustronny, pola zależne i blokady błędnych danych."""
import io, zipfile
from docx import Document
import pytest
from app.main import app

BASE={"dokumenty":"pb2","wybor_potwierdzony":"tak","inw-0-imie_nazwisko":"Julia Kontrolna","inw-0-miejscowosc":"Nowy Targ","inw-0-ulica":"ul. Testowa","inw-0-nr_domu":"12","inw-0-kod_pocztowy":"34-400","adres-miejscowosc":"Nowy Targ","adres-nr_domu":"12","adres-nr_dzialki":"1704/8","adres-identyfikator_dzialki":"121101_1.0001.1704/8","pb2-roboty":"Budowa wolnostojącego budynku gospodarczego o powierzchni zabudowy 24 m².","pb2-termin":"15.03.2027"}

def dokument(form):
    with app.test_client() as c: r=c.post('/generuj',data=form)
    assert r.status_code==200,r.get_data(as_text=True)
    with zipfile.ZipFile(io.BytesIO(r.data)) as z:
        assert z.namelist()==['PB-2_Julia_Kontrolna.docx']
        return Document(io.BytesIO(z.read(z.namelist()[0])))

def tekst(d):
    return '\n'.join([p.text for p in d.paragraphs]+[c.text for t in d.tables for row in t.rows for c in row.cells])

def test_pb2_dwie_strony_dane_z_obiegowki_i_zalaczniki():
    d=dokument(BASE|{"pb2-0-zal-oswiadczenie":"tak","pb2-0-zal-inne":"tak","pb2-0-zal-opis":"Mapa do celów projektowych"})
    t=tekst(d)
    for s in ['PB-2','Julia Kontrolna','Budowa wolnostojącego budynku gospodarczego','15.03.2027','1704/8','Mapa do celów projektowych','Dz. U. z 2026 r. poz. 3']:
        assert s in t
    assert '{{' not in t
    runs=[r for p in d.paragraphs for r in p.runs]
    checkboxy=[r for r in runs if r.style.name.startswith('PB2_ZAL_')]
    assert checkboxy and any(not r.font.strike for r in checkboxy)
    assert next(r for r in runs if r.style.name=='PB2_ZAL_OSWIADCZENIE').text.startswith('☒')
    assert next(r for r in runs if r.style.name=='PB2_ZAL_PELNOMOCNICTWO').text.startswith('☐')
    assert len(d.sections)==1

def test_dane_pelnomocnika_i_adres_korespondencyjny():
    d=dokument(BASE|{"pb2-0-typ_pelnomocnika":"pelnomocnik","pb2-0-proxy-imie_nazwisko":"Anna Przykładowa","pb2-0-proxy-kraj":"Polska","pb2-0-proxy-miejscowosc":"Rabka-Zdrój","pb2-0-koresp-miejscowosc":"Kraków"})
    t=tekst(d);assert 'Anna Przykładowa' in t and 'Kraków' in t
    typ=[r for p in d.paragraphs for r in p.runs if r.style.name.startswith('PB2_TYP_')]
    assert next(r for r in typ if r.style.name=='PB2_TYP_pelnomocnik').text.startswith('☒')
    assert '☐' in next(r for r in typ if r.style.name=='PB2_TYP_do_doreczen').text

def test_wyglad_stosuje_sie_do_wpisanych_wartosci():
    d=dokument(BASE|{'format-kolor':'granatowy','format-pogrubienie':'tak','format-rozmiar':'wiekszy'})
    runs=[r for p in d.paragraphs for r in p.runs]
    wartosc=next(r for r in runs if r.text==BASE['pb2-roboty'])
    assert wartosc.bold and str(wartosc.font.color.rgb)=='1F3864' and wartosc.font.size.pt==11

@pytest.mark.parametrize('zmiany,blad',[( {'pb2-roboty':''},'opisz rodzaj'),({'pb2-termin':'31.02.2027'},'poprawną datą'),({'pb2-termin':'2027-03-15'},'format DD.MM.RRRR'),({'pb2-0-typ_pelnomocnika':'pelnomocnik'},'podaj imię i nazwisko'),({'pb2-roboty':'X'*1201},'za długa')])
def test_bledne_pb2_nie_przechodzi(zmiany,blad):
    with app.test_client() as c:r=c.post('/generuj',data=BASE|zmiany)
    assert r.status_code==400 and blad in r.get_data(as_text=True)
