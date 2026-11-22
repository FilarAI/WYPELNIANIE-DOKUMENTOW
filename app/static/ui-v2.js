/* Lokalny interfejs v2: stan pracy bez wysyłania danych poza localhost. */
(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  function pokazPole(field) {
    if (!field) return;
    for (let p = field.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS') p.open = true;
    field.scrollIntoView({behavior: reduced() ? 'auto' : 'smooth', block: 'center'});
    field.focus({preventScroll: true});
  }
  // Ujednolicone typy kontrolek; nazwy formularzy i format żądania zostają bez zmian.
  $$('.pole input:not([type])').forEach(input => input.type = 'text');
  $$('.pole input').forEach(input => {
    if (input.type === 'text' && /(?:email|e-mail)$/.test(input.name)) input.type = 'email';
    if (input.type === 'text' && /(?:telefon|telefonu)$/.test(input.name)) input.type = 'tel';
    if (/pesel/.test(input.name)) { input.inputMode = 'numeric'; input.spellcheck = false; }
    if (['email', 'tel'].includes(input.type)) input.spellcheck = false;
  });
  // Każde źródło ma własny cykl: dodanie → odczyt → rodzaj → gotowość/błąd.
  const upload = $('#formularz-pliku');
  if (upload) {
    const rows = $$('.wiersz-zrodla', upload), drop = $('#pole-upload');
    const error = $('#blad-upload'), status = $('#status-upload'), submit = $('#wczytaj-pliki');
    upload.noValidate = true;
    const add = $('#dodaj-zrodlo'), picker = $('#pliki-zbiorcze');
    const states = new Map(rows.map(row => [row, {version:0, file:null, controller:null, state:'empty'}]));
    let busy = false, dragging = 0;
    upload.classList.add('upload-gotowy');
    const fileInput = row => $('input[type=file]',row);
    function symbol(kind) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
      svg.setAttribute('viewBox','0 0 24 24'); svg.setAttribute('fill','none'); svg.setAttribute('stroke','currentColor'); svg.setAttribute('stroke-width','2'); svg.setAttribute('stroke-linecap','round'); svg.setAttribute('stroke-linejoin','round'); svg.setAttribute('aria-hidden','true');
      const path = document.createElementNS('http://www.w3.org/2000/svg','path'); path.setAttribute('d',kind === 'ok' ? 'M5 12l4 4L19 6' : 'M6 6l12 12M18 6 6 18'); svg.append(path); return svg;
    }
    function fail(message) { error.textContent=message; error.hidden=false; error.focus(); }
    function validate(file) { return !/\.(docx|pdf)$/i.test(file.name) ? 'Nieobsługiwany format. Wybierz Word (.docx) lub PDF.' : !file.size ? 'Plik jest pusty. Wybierz inny dokument.' : file.size > 50*1024*1024 ? 'Plik przekracza limit 50 MB. Wybierz mniejszy dokument.' : ''; }
    function occupied() { return rows.filter(row => states.get(row).file); }
    function refresh() {
      const count=occupied().length, ready=occupied().filter(row=>states.get(row).state==='ready' && $('select',row).value).length;
      $('#liczba-plikow').textContent=`${count}/3`;
      $('#postep-plikow').setAttribute('aria-valuenow',String(count));
      $('#postep-plikow').setAttribute('aria-valuetext',`${count} z 3 miejsc zajętych. Gotowe: ${ready}.`);
      $('#wypelnienie-plikow').style.transform=`scaleX(${count/3})`;
      status.textContent=count ? `Dodane pliki: ${count}/3 · Gotowe do dalszej pracy: ${ready}` : 'Dodaj dokumenty. Każdy plik pojawi się poniżej z własnym rodzajem i statusem.';
      rows.forEach((row,i)=>{
        const state=states.get(row), select=$('select',row), file=state.file;
        row.hidden=!file; fileInput(row).required=false; select.required=Boolean(file);
        $('.plik-numer',row).textContent=`Plik ${i+1}`;
        $('.nazwa-upload',row).textContent=file?.name || `Plik ${i+1}`;
        row.dataset.stan=state.state;
        const line=$('.status-pliku',row); line.replaceChildren();
        if(file){
          if(state.state==='checking'){ const spinner=document.createElement('span'); spinner.className='status-spinner'; spinner.setAttribute('aria-hidden','true'); line.append(spinner); }
          else line.append(symbol(state.state==='ready'?'ok':'error'));
          const text=document.createElement('span'); text.textContent=state.message; line.append(text);
        }
        let meta=$('.upload-meta',row); if(!meta){meta=document.createElement('p');meta.className='upload-meta';row.append(meta);}
        const size=file ? (file.size < 1024*1024 ? new Intl.NumberFormat('pl',{maximumFractionDigits:0}).format(Math.ceil(file.size/1024))+' KB' : new Intl.NumberFormat('pl',{maximumFractionDigits:1}).format(file.size/1024/1024)+' MB') : '';
        meta.textContent=file ? `${size} · Dodano ${state.time} · ${state.method}` : '';
        const note=$('.typ-pliku-opis',row);
        note.textContent=state.state==='checking' ? 'Rozpoznaję rodzaj dokumentu… Możesz też wybrać go ręcznie.' : state.state==='ready' ? (select.value ? (state.manual ? 'Rodzaj wybrany ręcznie' : 'Podpowiedź na podstawie treści — sprawdź, czy jest poprawna') : 'Nie rozpoznano rodzaju jednoznacznie. Wybierz go z listy.') : '';
      });
      add.hidden=count===0 || count===3; add.textContent=count?'Dodaj kolejny plik':'Dodaj plik';
    }
    async function inspect(row, file, method){
      const previous=states.get(row); previous.controller?.abort();
      const state={version:previous.version+1,file,controller:new AbortController(),state:'checking',message:'Sprawdzam i odczytuję plik…',time:new Intl.DateTimeFormat('pl',{hour:'2-digit',minute:'2-digit'}).format(new Date()),method,manual:false};
      states.set(row,state); $('select',row).value=''; error.hidden=true;
      const localError=validate(file);
      if(localError){state.state='error';state.message=localError;refresh();return;}
      refresh();
      try {
        const body=new FormData(); body.append('plik',file);
        const response=await fetch('/sprawdz-plik',{method:'POST',body,signal:state.controller.signal});
        const result=await response.json(); if(!response.ok)throw new Error(result.blad || 'Nie udało się odczytać dokumentu.');
        if(states.get(row)!==state)return;
        if(!state.manual && result.typ)$('select',row).value=result.typ;
        state.state='ready';state.message=result.ocr?'Plik odczytany, także ze skanu':'Plik odczytany poprawnie';
      }catch(exception){
        if(exception.name==='AbortError'||states.get(row)!==state)return;
        state.state='error';state.message=exception.message==='Failed to fetch'?'Brak połączenia z aplikacją. Wybierz plik ponownie, aby spróbować jeszcze raz.':exception.message;
      }
      refresh();
    }
    function assign(files,method){
      if(busy || !files.length)return;
      const free=rows.filter(row=>!states.get(row).file);
      if(files.length>free.length)return fail('Możesz dodać maksymalnie 3 pliki. Usuń wybrany plik, aby zwolnić miejsce.');
      files.forEach((file,i)=>{const transfer=new DataTransfer();transfer.items.add(file);fileInput(free[i]).files=transfer.files;inspect(free[i],file,method);});
      const first=free[0]; if(first){first.scrollIntoView({behavior:reduced()?'auto':'smooth',block:'nearest'});$('select',first).focus({preventScroll:true});}
    }
    rows.forEach(row=>{
      const input=fileInput(row);input.tabIndex=-1;
      const button=document.createElement('button');button.type='button';button.className='przycisk przycisk-drugorzedny zmien-plik';button.textContent='Zmień plik';button.addEventListener('click',()=>input.click());input.after(button);
      const note=document.createElement('small');note.className='typ-pliku-opis';note.id='typ-opis-'+row.dataset.nr;$('select',row).setAttribute('aria-describedby',note.id);$('select',row).after(note);
      input.addEventListener('change',()=>{if(input.files[0])inspect(row,input.files[0],'Wybrano z dysku');});
      $('select',row).addEventListener('change',()=>{states.get(row).manual=true;refresh();});
      $('.usun-zrodlo',row).addEventListener('click',()=>{const old=states.get(row);old.controller?.abort();input.value='';$('select',row).value='';states.set(row,{version:old.version+1,file:null,state:'empty'});refresh();$('#wybierz-pliki').focus();});
    });
    $('#wybierz-pliki').addEventListener('click',()=>picker.click());
    add.addEventListener('click',()=>picker.click());
    picker.addEventListener('change',()=>{assign([...picker.files],'Wybrano z dysku');picker.value='';});
    ['dragenter','dragover','dragleave','drop'].forEach(name=>drop.addEventListener(name,event=>{
      event.preventDefault();if(name==='dragenter')dragging++;if(name==='dragleave')dragging=Math.max(0,dragging-1);
      if(name==='drop'){dragging=0;assign([...event.dataTransfer.files],'Przeciągnięto do aplikacji');}drop.classList.toggle('nad-polem',dragging>0);
    }));
    upload.addEventListener('submit',async event=>{
      event.preventDefault();if(busy)return;
      const files=occupied(); if(!files.length)return fail('Dodaj przynajmniej jeden plik.');
      const pending=files.find(row=>states.get(row).state==='checking');if(pending)return fail('Trwa sprawdzanie pliku. Poczekaj na wynik odczytu.');
      const invalid=files.find(row=>states.get(row).state==='error');if(invalid){fail('Popraw lub usuń plik oznaczony czerwonym X.');invalid.scrollIntoView({behavior:reduced()?'auto':'smooth',block:'center'});return;}
      const missing=files.find(row=>!$('select',row).value);if(missing){$('select',missing).focus();return;}
      const data=new FormData(upload),controls=$$('button,input,select',upload),previous=controls.map(control=>control.disabled);
      busy=true;controls.forEach(control=>control.disabled=true);submit.classList.add('wczytywanie');upload.setAttribute('aria-busy','true');error.hidden=true;
      $('.tekst-upload').textContent='Łączę dane z dokumentów…';status.textContent='Przygotowuję dane inwestycji z wybranych źródeł…';
      try{
        const response=await fetch(upload.action,{method:'POST',body:data,headers:{'X-Requested-With':'fetch'}});
        if(!(response.headers.get('Content-Type')||'').includes('application/json'))throw new Error('Nie udało się odczytać zestawu plików. Sprawdź ich rozmiar i spróbuj ponownie.');
        const result=await response.json();if(!response.ok)throw new Error(result.blad||'Nie udało się odczytać zestawu.');location.href='/wybierz-dokumenty?token='+encodeURIComponent(result.token);
      }catch(exception){fail(exception.message||'Nie udało się połączyć z lokalną aplikacją.');}
      finally{busy=false;controls.forEach((control,i)=>control.disabled=previous[i]);submit.classList.remove('wczytywanie');upload.removeAttribute('aria-busy');$('.tekst-upload').textContent='Odczytaj pliki';refresh();}
    });
    window.addEventListener('pageshow',()=>{busy=false;submit.disabled=false;upload.removeAttribute('aria-busy');submit.classList.remove('wczytywanie');$('.tekst-upload').textContent='Odczytaj pliki';rows.forEach(row=>{const file=fileInput(row).files[0];if(file && states.get(row).file!==file)inspect(row,file,'Przywrócono wybrany plik');});refresh();});
    refresh();
  }
  // Wybór dokumentów. Wyszukiwanie nie modyfikuje zaznaczeń ani porządku listy.
  const selection = $('#wybor-dokumentow');
  if (selection) {
    let category = 'wszystkie';
    const rows = $$('.dokument-wiersz', selection), search = $('#szukaj-dokumentow');
    const normal = value => value.toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ł/g, 'l');
    function update() {
      const query = normal(search.value.trim()); let visible = 0;
      rows.forEach(row => { row.hidden = !(category === 'wszystkie' || row.dataset.kategoria === category) || !normal(row.textContent).includes(query); if (!row.hidden) visible++; });
      $('#wynik-szukania').textContent = visible ? `Widoczne dokumenty: ${visible} z ${rows.length}` : 'Nie znaleziono dokumentów. Zmień nazwę, kod lub kategorię.';
      const selected = rows.filter(row => $('input', row).checked);
      $('#licznik-wyboru').textContent = `Wybrano: ${selected.length}`;
      $('#lista-wybranych').replaceChildren(...selected.map(row => { const li = document.createElement('li'); li.textContent = $('strong', row).textContent; return li; }));
      if (selected.length) $('#blad-wyboru').hidden = true;
    }
    $$('.filtry-dokumentow button').forEach(button => button.addEventListener('click', () => {
      category = button.dataset.filtr; $$('.filtry-dokumentow button').forEach(b => b.setAttribute('aria-pressed', String(b === button))); update();
    }));
    search.addEventListener('input', update); selection.addEventListener('change', update);
    selection.addEventListener('submit', e => { if (!rows.some(row => $('input', row).checked)) { e.preventDefault(); $('#blad-wyboru').hidden = false; $('#blad-wyboru').focus(); } });
    window.addEventListener('pageshow', update); update();
  }
  const form = $('#formularz');
  if (form) {
    const format = $('.format-danych', form);
    if (format) {
      form.prepend(format);
      const summary = $('summary', format);
      if (!$('.format-ikona', summary)) {
        const badge = document.createElement('span'); badge.className = 'format-ikona';
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', 'currentColor'); svg.setAttribute('stroke-width', '1.75'); svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round'); svg.setAttribute('aria-hidden', 'true'); svg.classList.add('ikona');
        ['M4 7V4h16v3','M12 4v16','M8 20h8'].forEach(d => { const path = document.createElementNS('http://www.w3.org/2000/svg', 'path'); path.setAttribute('d', d); svg.append(path); });
        badge.append(svg); summary.prepend(badge);
      }
    }
  }
  if (!form) { $$('.kontekst-pracy').forEach(panel => { const button = document.createElement('button'); button.type='button'; button.className='kontekst-toggle'; button.textContent='Wybrane dokumenty'; button.setAttribute('aria-expanded','false'); button.addEventListener('click',()=>{ const open=panel.classList.toggle('kontekst-otwarty'); button.setAttribute('aria-expanded',String(open)); }); panel.prepend(button); }); return; }
  // Odwzorowanie inwestorów ze szkicu zachowuje także dodane i usunięte osoby.
  const draft = JSON.parse($('#szkic-formularza').textContent);
  if (draft.length) {
    const ids = [...new Set(draft.map(([name]) => /^inw-(\d+)-/.exec(name)?.[1]).filter(Boolean))];
    if (ids.length) {
      const template = $('#wzor-inwestora').innerHTML;
      $('#inwestorzy').innerHTML = ids.map(id => template.replaceAll('__N__', id)).join('');
    }
    const values = new Map(); draft.forEach(([name, value]) => { if (!values.has(name)) values.set(name, []); values.get(name).push(value); });
    $$('input, textarea, select', form).forEach(field => {
      if (['dokumenty','token_wgrania','wybor_potwierdzony'].includes(field.name) || !field.name) return;
      if (['checkbox','radio'].includes(field.type)) field.checked = (values.get(field.name) || []).includes(field.value);
      else if (values.has(field.name)) field.value = values.get(field.name)[0];
    });
    if (typeof numeruj === 'function') numeruj();
  }
  // Panel kontekstu zajmuje jeden wiersz na wąskich ekranach.
  $$('.kontekst-pracy').forEach(panel => {
    const toggle = document.createElement('button'); toggle.type = 'button'; toggle.className = 'kontekst-toggle'; toggle.textContent = 'W tej sprawie'; toggle.setAttribute('aria-expanded', 'false');
    toggle.addEventListener('click', () => { const open = panel.classList.toggle('kontekst-otwarty'); toggle.setAttribute('aria-expanded', String(open)); }); panel.prepend(toggle);
  });
  // Dokumenty rozwijane, wspólna nawigacja po źródłowych sekcjach.
  const codes = new Map([['pb1','pb1-tytul'],['pb2','pb2-tytul'],['pb2a','pb2a-tytul'],['pb7','pb7-tytul'],['pb9','pb9-tytul'],['ba4','ba4-tytul'],['egib','egib-tytul'],['egib_wypis','egibw-tytul'],['formularz_p','p-tytul'],['os616','os616-tytul'],['pelnomocnictwo_egib','pel-egib-tytul']]);
  const sections = new Map();
  codes.forEach((id, code) => {
    const heading = document.getElementById(id); if (!heading) return;
    const section = heading.closest('section');
    const details = document.createElement('details'); details.className = 'sekcja dokument-szczegoly'; details.id = 'dokument-' + code; details.dataset.kod = code;
    const summary = document.createElement('summary'), title = document.createElement('h2'); title.textContent = heading.textContent; summary.append(title);
    section.before(details); details.append(summary, section); sections.set(code, details);
  });
  $$('#formularz > section:not([hidden]), #formularz > details').forEach((section, i) => {
    const heading = $('h2', section); if (!heading) return;
    if (!section.id) section.id = 'sekcja-' + i;
    const link = document.createElement('a'); link.href = '#' + section.id; link.textContent = heading.textContent.replace('Do sprawdzenia','').trim();
    link.addEventListener('click', e => { e.preventDefault(); if (section.tagName === 'DETAILS') section.open = true; section.tabIndex = -1; pokazPole(section); });
    $('#nawigacja-sekcji').append(link);
  });
  // Przejścia z ostrzeżeń: pole źródłowe może być zwykłym tekstem, którego nie edytujemy.
  $$('.lista-ostrzezen li').forEach(item => {
    const title = $('.ostrzezenie-nazwa', item).textContent.toLocaleLowerCase('pl');
    const target = title.includes('inwestor') ? $('#inwestorzy input') : title.includes('adres') ? $('[name="adres-miejscowosc"]') : title.includes('nazwa') ? $('[name="nazwa_inwestycji"]') : null;
    if (target) { const button = document.createElement('button'); button.type = 'button'; button.className = 'przycisk-tekstowy'; button.textContent = 'Przejdź do pola'; button.addEventListener('click', () => pokazPole(target)); item.append(button); }
  });
  const actions = $('.pasek-generowania', form); if (actions) form.append(actions);
  // Czytelny status na podstawie serwerowych walidatorów wybranych dokumentów.
  const status = $('#status-walidacji'), tasks = $('#zadania-lista'), exportStatus = $('#status-generowania');
  let timer, currentRequest, lastValidation = null, generationBusy = false, pauseChecks = false;
  function nativeIssues() {
    const radioNames = new Set();
    return $$('input,select,textarea', form).filter(field => {
      if (!field.willValidate || field.disabled || !field.name || field.type === 'hidden') return false;
      if (field.type === 'radio') { if (radioNames.has(field.name)) return false; radioNames.add(field.name); }
      return !field.validity.valid;
    });
  }
  function markFields() {
    $$('.walidacja-pola', form).forEach(el => { const field = document.querySelector('[aria-describedby="' + el.id + '"]'); field?.removeAttribute('aria-describedby'); el.remove(); });
    $$('.pole-bledne', form).forEach(el => { el.classList.remove('pole-bledne'); el.removeAttribute('aria-invalid'); });
    const invalid = nativeIssues();
    invalid.forEach((field, index) => {
      field.classList.add('pole-bledne'); field.setAttribute('aria-invalid', 'true');
      const message = document.createElement('small'); message.className = 'walidacja-pola'; message.id = 'blad-pola-' + index; message.textContent = field.validationMessage;
      field.setAttribute('aria-describedby', message.id); field.after(message);
    });
    return invalid;
  }
  async function check() {
    clearTimeout(timer); currentRequest?.abort(); currentRequest = new AbortController();
    const controller = currentRequest;
    try {
      const response = await fetch('/sprawdz-dane', {method:'POST', body:new FormData(form), signal:controller.signal});
      const result = await response.json(); lastValidation = result;
      tasks.replaceChildren();
      result.zadania.forEach(task => {
        const li = document.createElement('li'), title = document.createElement('strong'), text = document.createElement('p'), button = document.createElement('button');
        const section = sections.get(task.kod);
        title.textContent = section ? $('summary h2', section).textContent : 'Dane wspólne'; text.textContent = task.opis;
        button.type = 'button'; button.className = 'przycisk-tekstowy'; button.textContent = 'Przejdź do danych';
        button.addEventListener('click', () => { if (section) section.open = true; const field = nativeIssues().find(f => !section || section.contains(f)); if (!field && section) section.tabIndex = -1; pokazPole(field || section || form); });
        li.append(title,text,button); tasks.append(li);
      });
      const count = result.zadania.length;
      status.textContent = count ? `Dokumenty z danymi do poprawy: ${count}. Poniżej pokazujemy pierwszą wskazówkę dla każdego dokumentu.` : 'Walidacja dokumentów zakończona. Sprawdź jeszcze zgodność danych ze źródłami.';
      exportStatus.textContent = result.wygaslo ? 'Wygasły pliki źródłowe' : count ? `Dokumenty wymagające poprawy: ${count}` : 'Dane przeszły walidację · sprawdź rozbieżności w źródłach';
      return result;
    } catch (error) {
      if (error.name !== 'AbortError') { lastValidation = null; status.textContent = 'Nie udało się sprawdzić danych. Sprawdź połączenie z lokalną aplikacją.'; exportStatus.textContent = 'Sprawdzenie danych niedostępne'; }
      return null;
    }
  }
  function schedule() { if (pauseChecks || generationBusy) return; status.textContent = 'Sprawdzam zmiany…'; clearTimeout(timer); timer = setTimeout(check, 600); }
  form.addEventListener('input', schedule); form.addEventListener('change', schedule); document.addEventListener('filar:zmiana', schedule);
  const back = $('#powrot-wybor');
  back?.addEventListener('click', async event => { event.preventDefault(); const result = await check(); if (result && !result.wygaslo) location.href = back.href; else pokazPole(status); });
  // Walidacja i wynik pozostają na stronie: po błędzie użytkownik nie traci formularza.
  const errorBox = $('#blad-generowania');
  // Krok 4: ekran sukcesu w tej samej stronie, żeby „Wróć do formularza” nie gubił wpisanych danych.
  const steps = $$('.kroki .krok'), stepsHtml = steps.map(step => [step.className, step.querySelector('.krok-kolko').innerHTML]);
  function pokazGotowe(on) {
    $('#tresc > .wejscie:not(#ekran-gotowe)').hidden = on; $('#tresc > .uklad-pracy').hidden = on; $('#ekran-gotowe').hidden = !on;
    steps.forEach((step, i) => { step.className = on ? (i < 3 ? 'krok ukonczony' : 'krok aktywny') : stepsHtml[i][0];
      step.querySelector('.krok-kolko').innerHTML = on && i < 3 ? stepsHtml[0][1] : stepsHtml[i][1];
      if (step.className.includes('aktywny')) step.setAttribute('aria-current', 'step'); else step.removeAttribute('aria-current'); });
    window.scrollTo(0, 0); if (on) $('#gotowe-tytul').focus();
  }
  $('#gotowe-wroc')?.addEventListener('click', () => pokazGotowe(false));
  form.addEventListener('submit', async event => {
    event.preventDefault(); if (generationBusy) return;
    const invalid = markFields();
    if (invalid.length) { pokazPole(invalid[0]); schedule(); return; }
    generationBusy = true; if ($('#przycisk-zapisz')) { $('#przycisk-zapisz').classList.add('w-toku'); $('.etykieta', $('#przycisk-zapisz')).textContent = 'Generuję dokumenty…'; } clearTimeout(timer); form.classList.add('generowanie-zajete'); form.setAttribute('aria-busy','true');
    errorBox.hidden = true; exportStatus.textContent = 'Generuję dokumenty…';
    const buttons = $$('button,input,select,textarea', form), disabled = buttons.map(button => button.disabled);
    const data = new FormData(form); data.set('akcja', event.submitter?.value || 'zapisz'); buttons.forEach(button => button.disabled = true);
    try {
      const response = await fetch(form.action, {method:'POST', body:data, headers:{'X-Requested-With':'fetch'}});
      const json = (response.headers.get('Content-Type') || '').includes('application/json');
      if (!response.ok) { const body = json ? (await response.json()).blad : await response.text(); throw new Error(response.status >= 500 ? 'Nie udało się wygenerować dokumentów. Spróbuj ponownie lub sprawdź folder zapisu.' : body); }
      let names, folder = '';
      if (json) {
        const result = await response.json(); names = result.pliki; folder = result.folder;
        $('#gotowe-tytul').textContent = 'Gotowe – dokumenty zapisane';
        $('#gotowe-opis').textContent = names.length === 1 ? 'Zapisano 1 dokument.' : `Zapisano dokumenty: ${names.length}.`;
      } else {
        const blob = await response.blob(), url = URL.createObjectURL(blob), link = document.createElement('a');
        const header = response.headers.get('Content-Disposition') || '', utf = /filename\*=UTF-8''([^;]+)/.exec(header)?.[1];
        const name = (utf && decodeURIComponent(utf)) || /filename="([^"]+)"/.exec(header)?.[1] || 'Dokumenty_FILAR.zip';
        link.href = url; link.download = name; link.click(); names = [name]; folder = '~/Downloads';
        $('#gotowe-tytul').textContent = 'Gotowe – archiwum ZIP pobrane';
        $('#gotowe-opis').textContent = 'Plik ZIP jest w folderze Pobrane.';
      }
      $('#gotowe-pliki').replaceChildren(...names.map(name => { const li = $('#wzor-pliku').content.firstElementChild.cloneNode(true); $('.plik-nazwa', li).textContent = name; return li; }));
      $('#gotowe-folder').textContent = folder; $('#gotowe-sciezka').hidden = !json; $('#gotowe-komunikat').hidden = true;
      $('#gotowe-finder').onclick = async () => { const msg = $('#gotowe-komunikat'); try { const body = new FormData(); body.set('folder', folder); const response = await fetch('/pokaz-folder',{method:'POST',body}); if (!response.ok) throw new Error(); msg.hidden = true; } catch { msg.textContent = 'Nie udało się otworzyć Findera. Folder: ' + folder; msg.hidden = false; } };
      pokazGotowe(true); exportStatus.textContent = 'Dokumenty wygenerowane. Możesz poprawić dane i wygenerować ponownie.';
    } catch (error) {
      errorBox.textContent = error.message || 'Nie udało się połączyć z aplikacją.'; errorBox.hidden = false; pokazPole(errorBox); exportStatus.textContent = 'Nie wygenerowano dokumentów. Popraw wskazane dane i spróbuj ponownie.';
    } finally {
      generationBusy = false; form.classList.remove('generowanie-zajete'); form.removeAttribute('aria-busy'); buttons.forEach((button,i) => button.disabled = disabled[i]);
      const save = $('#przycisk-zapisz'); if (save) { save.classList.remove('w-toku'); $('.etykieta',save).textContent = 'Zapisz dokumenty w folderze'; }
    }
  });
  window.addEventListener('pageshow', () => { pauseChecks = false; check(); });
  check();
})();
