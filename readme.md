# BrytonSync v2.0.0

Sincronizzazione automatica tra **Bryton Active**, **Intervals.icu** e **Dropbox**.

BrytonSync permette di:

* scaricare automaticamente le attività da Bryton Active
* caricare le attività su Intervals.icu
* archiviare i file FIT su Dropbox
* sincronizzare i workout pianificati da Intervals.icu verso i dispositivi Bryton
* utilizzare l'app sia da Desktop che da Android

---

## Features

### Attività Bryton → Intervals.icu

* Login automatico Bryton Active
* Download attività recenti
* Download FIT diretto da Bryton
* Upload automatico su Intervals.icu
* Gestione duplicati tramite External ID
* Gestione attività cancellate

### Attività Bryton → Dropbox

* Upload automatico FIT
* Cartella Dropbox personalizzabile
* OAuth Dropbox PKCE
* Nessun App Secret richiesto

### Workout Intervals.icu → Bryton

* Download workout pianificati
* Upload automatico su Bryton Active
* Supporto workout basati sulla potenza
* Supporto workout basati sulla frequenza cardiaca
* Supporto intervalli e ripetizioni
* Compatibile con dispositivi Bryton Rider

### Applicazioni incluse

* GUI Desktop (Flet)
* APK Android
* CLI Python

---

## Installazione

### Desktop

```bash
pip install -r requirements.txt
python main.py
```

### Android

Installare l'APK disponibile nella sezione Releases.

---

## Configurazione

### Bryton Active

Inserire:

* Email Bryton
* Password Bryton

### Intervals.icu

Inserire:

* API Key
* Athlete ID

### Dropbox

Premere:

```text
Collega Dropbox
```

e completare l'autorizzazione tramite browser.

---

## Utilizzo

### Sync Uscite

Sincronizza:

```text
Bryton Active → Intervals.icu
Bryton Active → Dropbox
```

### Sync Workout

Sincronizza:

```text
Intervals.icu → Bryton Active
```

### Sync Completa

Esegue entrambe le sincronizzazioni.

---

## CLI

### Attività

```bash
python -m brytonsync.cli activities
```

### Workout

```bash
python -m brytonsync.cli workouts --days 14
```

### Sync completa

```bash
python -m brytonsync.cli all --days 14
```

---

## Versione 2.0.0

### Nuove funzionalità

* Sync attività Bryton → Intervals.icu
* Sync attività Bryton → Dropbox
* Sync workout Intervals.icu → Bryton
* Supporto workout Potenza
* Supporto workout Frequenza Cardiaca
* Dropbox OAuth PKCE
* GUI Desktop Flet
* APK Android
* Gestione FIT diretti Bryton
* Gestione attività cancellate
* Prevenzione duplicati

---

## Roadmap

* Miglioramento interfaccia grafica
* Backup automatici
* Migliore gestione errori
* Distribuzione APK tramite GitHub Releases

---

## Disclaimer

BrytonSync è un progetto indipendente e non è affiliato, sponsorizzato o approvato da Bryton, Intervals.icu o Dropbox.

---

## License

MIT License
