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


def test_miasto_z_identyfikatora():
    assert teryt.miasto_z_identyfikatora("120903_4.0002.1358") == "Myślenice"   # miasto w gminie miejsko-wiejskiej
    assert teryt.miasto_z_identyfikatora("121701_1.0005.245/7") == "Zakopane"   # gmina miejska
    assert teryt.miasto_z_identyfikatora("146510_8.0101.12") == "Warszawa"      # dzielnica Warszawy
    assert teryt.miasto_z_identyfikatora("120904_2.0010.555/1") == ""           # wieś – kod nie wskazuje miejscowości
    assert teryt.miasto_z_identyfikatora("brak") == ""
