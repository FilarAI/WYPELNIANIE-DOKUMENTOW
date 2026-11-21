"""Rodzaj dokumentu wynika z odczytu treści, a uszkodzone źródło ma błąd."""
import io
import pytest
from docx import Document
from app.main import app


def docx(text):
    document=Document();document.add_paragraph(text);out=io.BytesIO();document.save(out);return out.getvalue()


@pytest.mark.parametrize('text,typ',[
    ('Obiegówka projektu. Inwestor Anna Nowak. Adres inwestycji: Rabka-Zdrój.', 'obiegowka'),
    ('DECYZJA nr 1/2026. Zatwierdzam projekt i udzielam pozwolenia na budowę.', 'decyzja'),
    ('Projekt budowlany. Projekt zagospodarowania terenu.', 'teczka'),
    ('Dokument z tekstem bez rozpoznawalnego rodzaju źródła.', ''),
])
def test_podpowiedz_z_tresci_a_nie_nazwy(text,typ):
    with app.test_client() as c:
        response=c.post('/sprawdz-plik',data={'plik':(io.BytesIO(docx(text)),'dokument.docx')})
        assert response.status_code==200
        assert response.json['typ']==typ and response.json['stan']=='odczytany'


@pytest.mark.parametrize('content,name',[
    (b'niepoprawny Word','dokument.docx'),(b'niepoprawny PDF','dokument.pdf'),
    (b'','pusty.docx'),(b'tekst','plik.txt'),(docx(''),'pusty.docx'),
])
def test_blad_zamiast_pozornego_sukcesu(content,name):
    with app.test_client() as c:
        response=c.post('/sprawdz-plik',data={'plik':(io.BytesIO(content),name)})
        assert response.status_code==400 and response.json['blad']


def test_wymagany_plik():
    with app.test_client() as c:
        assert c.post('/sprawdz-plik').status_code==400
