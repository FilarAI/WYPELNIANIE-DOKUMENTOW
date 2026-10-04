from app import teryt


def test_identyfikator_dzialki():
    j = teryt.z_identyfikatora("120903_4.0002.1358")
    assert (j.wojewodztwo, j.powiat, j.gmina) == ("małopolskie", "myślenicki", "Myślenice")


def test_identyfikator_nieznany():
    assert teryt.z_identyfikatora("999999_9.0001.1") is None
    assert teryt.z_identyfikatora("brak") is None


def test_miejscowosc_jednoznaczna():
    j = teryt.z_miejscowosci("Rabka-Zdrój")
    assert (j.wojewodztwo, j.powiat, j.gmina) == ("małopolskie", "nowotarski", "Rabka-Zdrój")


def test_miejscowosc_niejednoznaczna_bez_podpowiedzi():
    # "Zawada" występuje w wielu gminach w Polsce.
    assert teryt.z_miejscowosci("Zawada") is None


def test_miejscowosc_niejednoznaczna_z_podpowiedzia_z_dzialki():
    j = teryt.z_miejscowosci("Zawada", "120903_4.0002.1358")
    assert (j.wojewodztwo, j.powiat) == ("małopolskie", "myślenicki")
