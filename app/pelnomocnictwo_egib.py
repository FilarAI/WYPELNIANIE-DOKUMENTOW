"""Dane do pełnomocnictwa do spraw EGiB."""
import io,re
from docx import Document
from app.konfiguracja import PELNOMOCNIK

def odczytaj(form,dane):
 osoby=[]
 for i,osoba in enumerate(dane.get('inwestorzy',[])):
  pola={k:form.get(f'pel-egib-{i}-{k}','').strip() for k in ('dowod','organ','pesel')}
  if any(len(v)>({'dowod':30,'organ':120,'pesel':11}[k]) or any(ord(c)<32 for c in v) for k,v in pola.items()):raise ValueError('Pełnomocnictwo EGiB: sprawdź długość danych osobowych.')
  if not re.fullmatch(r'\d{11}',pola['pesel']):raise ValueError(f"Pełnomocnictwo EGiB: podaj 11-cyfrowy PESEL osoby „{osoba.get('imie_nazwisko','')}”.")
  if not pola['dowod'] or not pola['organ']:raise ValueError('Pełnomocnictwo EGiB: podaj numer dowodu i organ, który go wydał.')
  adres=', '.join(x for x in [' '.join(x for x in [osoba.get('ulica',''),osoba.get('nr_domu','')+('/'+osoba['nr_lokalu'] if osoba.get('nr_lokalu') else '')] if x), ' '.join(x for x in [osoba.get('kod_pocztowy',''),osoba.get('miejscowosc','')]) ] if x)
  osoby.append({'nazwa':osoba.get('imie_nazwisko',''),'adres':adres,'dowod':pola['dowod'],'organ':pola['organ'],'pesel':pola['pesel']})
 zakres=form.get('pel-egib-zakres','')
 if zakres not in {'samodzielnie','podpisany'}:raise ValueError('Pełnomocnictwo EGiB: wybierz właściwy zakres pełnomocnictwa.')
 pel={k:form.get('pel-egib-pelnomocnik-'+k,'').strip() for k in ('dowod','organ','pesel')}
 if not pel['dowod'] or not pel['organ'] or not re.fullmatch(r'\d{11}',pel['pesel']):raise ValueError('Pełnomocnictwo EGiB: uzupełnij numer dowodu, organ wydający i 11-cyfrowy PESEL pełnomocnika.')
 return {'osoby':osoby,'pelnomocnik':pel,'zakres':zakres,'data':form.get('data_pelnomocnictwa','').strip()}

def kontekst(dane):
 p=dane['pelnomocnictwo_egib'];osoby=p['osoby']
 return {'miejsce_data':f"{'.'*45} dn. {p['data'] or '.'*16}",'mocodawcy':'\n'.join(f"{o['nazwa']}\nzamieszkały/a w {o['adres']}\nlegitymujący/a się dowodem osobistym nr {o['dowod']} wydanym przez {o['organ']}\nposiadający/a numer PESEL {o['pesel']}" for o in osoby),
 'pelnomocnik':PELNOMOCNIK['imie_nazwisko'],'dowod_pelnomocnika':p['pelnomocnik']['dowod'],'organ_pelnomocnika':p['pelnomocnik']['organ'],'pesel_pelnomocnika':p['pelnomocnik']['pesel'],
 'adres_pelnomocnika':f"{PELNOMOCNIK['ulica']} {PELNOMOCNIK['nr_domu']}/{PELNOMOCNIK['nr_lokalu']}, {PELNOMOCNIK['kod_pocztowy']} {PELNOMOCNIK['miejscowosc']}",
 'zadanie':'złożeniem wniosku o wypis/wyrys z rejestru EGiB i odbiór dokumentu przez pełnomocnika' if p['zakres']=='samodzielnie' else 'złożeniem wniosku o wypis/wyrys z rejestru EGiB wypełnionego i podpisanego przez właściciela/władającego nieruchomością i odbiór w/w dokumentu przez pełnomocnika',
 'podpisy':'\n\n'.join('........................................................\n'+o['nazwa'] for o in osoby)}

def zastosuj(zawartosc,wybrane):
 d=Document(io.BytesIO(zawartosc));sel=wybrane['zakres']
 for p in d.paragraphs:
  for r in p.runs:
   if r.style.name=='PELEGIB_CHECK_samodzielnie':r.text='☒' if sel=='samodzielnie' else '☐'
   if r.style.name=='PELEGIB_CHECK_podpisany':r.text='☒' if sel=='podpisany' else '☐'
 out=io.BytesIO();d.save(out);return out.getvalue()
