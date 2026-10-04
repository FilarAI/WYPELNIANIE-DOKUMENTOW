"""Stałe dane biura używane przy wypełnianiu dokumentów."""

# Osoba upoważniona do złożenia PB-5 w imieniu inwestora (pełnomocnik biura).
# Wstawiana do PB-5 tylko po zaznaczeniu tej opcji w formularzu.
PELNOMOCNIK = {
    "imie_nazwisko": "Bartłomiej Filar",
    "kraj": "Polska",
    "wojewodztwo": "małopolskie",
    "powiat": "nowotarski",
    "gmina": "Rabka-Zdrój",
    "ulica": "Sądecka",
    "nr_domu": "33h",
    "nr_lokalu": "11",
    "miejscowosc": "Rabka-Zdrój",
    "kod_pocztowy": "34-700",
    "poczta": "Rabka-Zdrój",
}

# Wpisywane w puste pola, żeby można je było uzupełnić długopisem.
PUSTE_POLE = "……………………"

# „Nr lokalu” w PB-5, gdy adres jest podany, ale bez mieszkania (dom jednorodzinny).
BRAK_LOKALU = "–"
