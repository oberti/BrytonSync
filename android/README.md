# BrytonSync Android/Flet

App stile `igpsport-intervals` per sincronizzare:

```text
Bryton Active -> FIT -> intervals.icu -> Dropbox
```

## Dropbox OAuth PKCE

La GUI include un pulsante **Collega Dropbox**. Non devi inserire una Dropbox App Key.

Flusso:

1. Premi **Collega Dropbox**.
2. Si apre Dropbox nel browser.
3. Autorizza l'app.
4. Copia il codice mostrato da Dropbox.
5. Incollalo in **Codice autorizzazione Dropbox**.
6. Premi **Salva codice Dropbox**.
7. L'app salva il refresh token nelle impostazioni.

La cartella Dropbox è configurabile nel campo **Cartella Dropbox**, ad esempio:

```text
/BrytonSync
/Allenamenti/Bryton
```

## Avvio desktop per test

```powershell
cd C:\brytonsync_android
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
flet run main.py
```

## Build APK

```powershell
flet build apk --verbose
```

## Note

- `Intervals Athlete ID` va inserito solo numerico, senza `i`.
- I file FIT vengono nominati come `YYMMDDHHMMSS.fit` usando l'ora effettiva di partenza convertita nel fuso locale del dispositivo.
- Dropbox usa OAuth PKCE con refresh token, quindi non serve salvare access token temporanei.
