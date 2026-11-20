"""Walidacja bez generowania, szkic i eksport w nowym przepływie UI."""
import io
import re
import zipfile
from pathlib import Path
from app.main import app
from test_pb1 import BASE


def zaladuj(client):
    path = Path(__file__).parent / 'fixtures' / 'obiegowka_testowa_pelna.docx'
    r = client.post('/wybierz-dokumenty', data={'obiegowka': (io.BytesIO(path.read_bytes()), path.name)})
    return re.search(rb'name="token" value="([^"]+)', r.data).group(1).decode()


def test_walidacja_uzywa_regul_dokumentu_i_zachowuje_szkic():
    with app.test_client() as client:
        token = zaladuj(client)
        data = BASE | {'token_wgrania': token, 'pb1-nazwa': ''}
        r = client.post('/sprawdz-dane', data=data)
        assert r.status_code == 200
        assert r.json['zadania'][0]['kod'] == 'pb1'
        r = client.post('/podglad', data={'token': token, 'dokumenty': 'pb1'})
        assert b'szkic-formularza' in r.data and b'Krzysztof Testowy' in r.data
        r = client.post('/sprawdz-dane', data=BASE | {'token_wgrania': token})
        assert r.json['zadania'] == []  # Puste pola opcjonalne i brak pełnomocnika są dozwolone.


def test_wygasly_token_i_powrot_do_wyboru():
    with app.test_client() as client:
        assert client.post('/sprawdz-dane', data={'token_wgrania': 'wygasly'}).status_code == 400
        assert client.get('/wybierz-dokumenty?token=wygasly').status_code == 400
        token = zaladuj(client)
        r = client.get('/wybierz-dokumenty', query_string={'token': token, 'dokumenty': 'pb1'})
        assert r.status_code == 200 and b'value="pb1" checked' in r.data


def test_ajax_zip_i_blad_generowania():
    with app.test_client() as client:
        r = client.post('/generuj', data=BASE | {'akcja': 'zip'}, headers={'X-Requested-With':'fetch'})
        assert r.status_code == 200
        with zipfile.ZipFile(io.BytesIO(r.data)) as archive:
            assert archive.namelist() == ['PB-1_Krzysztof_Testowy.docx']
        r = client.post('/generuj', data=BASE | {'pb1-nazwa': ''}, headers={'X-Requested-With':'fetch'})
        assert r.status_code == 400 and 'podaj ogólną nazwę' in r.text


def test_ajax_zapis_zwraca_prawdziwe_pliki(tmp_path, monkeypatch):
    monkeypatch.setattr('app.main.zapis.zapamietaj_folder', lambda folder: None)
    with app.test_client() as client:
        r = client.post('/generuj', data=BASE | {'akcja':'zapisz','folder_zapisu':str(tmp_path)}, headers={'X-Requested-With':'fetch'})
        assert r.status_code == 200 and r.json['pliki'] == ['PB-1_Krzysztof_Testowy.docx']
        assert (tmp_path / r.json['pliki'][0]).exists()


def test_ajax_upload_i_blad_bez_nawigacji():
    with app.test_client() as client:
        r = client.post('/wybierz-dokumenty', data={}, headers={'X-Requested-With':'fetch'})
        assert r.status_code == 400 and r.json['blad']
        path = Path(__file__).parent / 'fixtures' / 'obiegowka_testowa_pelna.docx'
        r = client.post('/wybierz-dokumenty', data={'obiegowka':(io.BytesIO(path.read_bytes()),path.name)}, headers={'X-Requested-With':'fetch'})
        assert r.status_code == 200 and r.json['token']
        assert client.get('/wybierz-dokumenty',query_string={'token':r.json['token']}).status_code == 200
