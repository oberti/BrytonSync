# BrytonSync

Sincronizzatore sperimentale **Bryton Active -> file FIT -> intervals.icu**.

Derivato dagli endpoint ricostruiti dall'APK Bryton Active:

- `POST https://m2.brytonactive.com/api/login`
- `GET https://m2.brytonactive.com/api/activity?since=0&limit=...`
- `GET https://m2.brytonactive.com/api/activity?id=...`
- download FIT da URL dinamico trovato nel dettaglio attività
- header autenticati: `X-User-Id`, `X-Auth-Token`

## Installazione

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Modifica `.env` con email/password Bryton e, se vuoi caricare su intervals.icu, anche `INTERVALS_API_KEY` e `INTERVALS_ATHLETE_ID`.

## Test 1: solo login

```bash
python test_login.py
```

## Test 2: lista attività

```bash
python test_list.py
```

## Sync completo

Solo download FIT:

```bash
python -m brytonsync.cli
```

Upload anche su intervals.icu:

```env
UPLOAD_INTERVALS=true
INTERVALS_API_KEY=...
INTERVALS_ATHLETE_ID=i12345
```

poi:

```bash
python -m brytonsync.cli
```

## Nota importante su AESUtil

Il codice APK mostra che il campo `login` del JSON remoto viene decifrato con:

```java
AESUtil.decrypt(value, "G9uX0Fjd")
```

Nel materiale incollato non c'era ancora `AESUtil.java`. Ho quindi implementato un decrypt tollerante che prova le varianti AES Android più comuni. Se `test_login.py` dà errore tipo:

```text
Impossibile decifrare il campo 'login'
```

serve incollare `AESUtil.java`, oppure inserire manualmente nel codice il `loginPwdKey` già decifrato.

## Sicurezza

Non caricare `.env` su GitHub. Contiene credenziali.
