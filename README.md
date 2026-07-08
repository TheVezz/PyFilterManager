# Gestionale Filtri

Applicazione desktop per la gestione di filtri industriali con interfaccia **PySide6 + Fluent Design**, database relazionale e report stampabili.

## Panoramica

L'app è organizzata in quattro aree principali:

- `Home`: dashboard con riepilogo rapido dei filtri
- `Filtri`: gestione operativa di gerarchia, ricerca, card filtro e dettaglio quadro
- `Report`: riepilogo filtrabile e stampabile dei quadri per stato
- `Impostazioni`: preferenze di tema, lingua e formato date

Funzionalità già disponibili:

- gerarchia `sede -> reparto -> linea -> quadro elettrico`
- creazione, modifica, eliminazione e spostamento dei nodi della gerarchia
- creazione del quadro insieme al relativo filtro
- card filtro responsive con badge stato
- ricerca testuale con selezione dell'ambito
- filtro multiplo per stato
- dettaglio quadro con storico interventi
- report con stampa PDF
- localizzazione **italiano / inglese**
- rilevamento lingua del sistema operativo
- preferenze persistenti per tema, lingua e formato data

## Requisiti

- Python 3.10+
- Windows, macOS o Linux

## Installazione

```powershell
git clone <url-repository>
cd filtri

python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate    # macOS / Linux

pip install -e ".[dev]"
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
```

L'extra `dev` include **Factory Boy** per dati di sviluppo.

### Driver database opzionali

```powershell
pip install -e ".[postgres]"   # PostgreSQL
pip install -e ".[mysql]"      # MySQL
pip install -e ".[mariadb]"    # MariaDB
pip install -e ".[mssql]"      # SQL Server
pip install -e ".[oracle]"     # Oracle
pip install -e ".[all-db]"     # tutti i driver
```

## Avvio rapido

```powershell
# 1. Configura l'ambiente
copy .env.example .env

# 2. Crea dati di esempio
filtri-db seed --clear

# 3. Avvia l'app
filtri
```

Oppure:

```powershell
python main.py
```

All'avvio l'app applica automaticamente le migrazioni pendenti.

### Script Windows

Nella root del progetto sono presenti due script di utilita:

- `setup.bat`: installazione o disinstallazione del progetto nella `.venv`
- `start.bat`: avvio rapido dell'app

#### `setup.bat`

`setup.bat` crea la `.venv` se manca, aggiorna `pip`, installa il progetto e crea `.env` da `.env.example` se necessario.

Profili disponibili:

- `standard`
- `dev`
- `audit`
- `security`
- `quality`

Sono supportate anche combinazioni multiple dal menu interattivo, per esempio:

- `dev,audit`
- `dev,security`
- `dev,quality`
- `audit,quality`
- `security,quality`
- `audit,security`
- `dev,audit,security`
- `dev,audit,security,quality`

Esempi:

```powershell
.\setup.bat
.\setup.bat install
.\setup.bat install dev
.\setup.bat install audit
.\setup.bat install security
.\setup.bat install quality
.\setup.bat uninstall
```

#### `start.bat`

`start.bat` avvia l'app usando la `.venv` del progetto.

Comportamento:

- usa `pythonw.exe` se disponibile, così l'app parte senza console visibile
- se `.env` manca ma esiste `.env.example`, lo crea automaticamente
- se la `.venv` non esiste, chiede prima di eseguire `setup.bat`

Avvio:

```powershell
.\start.bat
```

## Interfaccia

L'app usa `FluentWindow` di `PySide6-Fluent-Widgets` con navigazione laterale:

- `Home`
- `Filtri`
- `Report`
- `Impostazioni` in basso nella sidebar

Il titolo mostrato all'utente è `Gestionale Filtri`, mentre il nome tecnico del pacchetto Python è `gestionale-filtri`.

## Home

La home è una dashboard sintetica con tre card:

- `Filtri in regola`
- `Filtri in scadenza`
- `Filtri scaduti`

Serve come colpo d'occhio iniziale sullo stato generale dell'impianto.

## Vista Filtri

La vista `Filtri` è divisa in due pannelli:

- a sinistra: contenuto operativo
- a destra: albero gerarchico della struttura

La TreeView rappresenta:

```text
sede -> reparto -> linea -> quadro elettrico
```

Toolbar disponibile sulla struttura:

- `Crea`
- `Modifica`
- `Elimina`
- `Sposta`
- `Espandi tutto`
- `Collassa tutto`

### Comportamento del pannello sinistro

- nessuna selezione: messaggio guida
- selezione di `sede`, `reparto` o `linea`: griglia di card filtro
- selezione di `quadro elettrico`: pannello dettaglio quadro

Quando si apre il dettaglio di un quadro, la barra di ricerca e filtro viene nascosta per lasciare più spazio al contenuto.

### Ricerca e filtri

La barra superiore della vista `Filtri` include:

- ricerca testuale
- scelta dei campi di ricerca
- filtro multiplo per stato
- pulsante `Reset`

Campi ricercabili:

- `quadro`
- `reparto`
- `linea`
- `dimensione`
- `frequenza`
- `quantità`

L'ambito dei campi cambia in base al nodo selezionato.

Stati filtro disponibili:

- `Tutti`
- `In regola`
- `In scadenza`
- `Scaduti`

Se vengono selezionati tutti gli stati specifici, il controllo torna automaticamente a `Tutti`.

### Card filtro

Ogni card mostra:

- nome quadro elettrico
- dimensione
- quantità filtri
- frequenza intervento
- ultimo intervento
- badge stato

Badge stato:

| Simbolo | Stato tecnico | Significato |
|---------|---------------|-------------|
| `✓` | `ok` | intervento ancora nei tempi |
| `!` | `warning` | intervento in scadenza |
| `✗` | `overdue` | intervento scaduto o assente |

## Creazione e modifica quadro

Quando si crea un quadro da una `linea`, il dialogo raccoglie:

- nome quadro elettrico
- quantità filtri
- dimensione filtri
- frequenza intervento
- data primo intervento
- configurazione `in scadenza`

Quando si modifica un quadro:

- vengono aggiornati sia quadro sia filtro
- la data del primo intervento non viene più richiesta
- resta disponibile la configurazione avanzata dello stato `in scadenza`

La logica interna usa ancora i campi `preavviso_*`, ma in UI la terminologia mostrata è `in scadenza`.

## Validazioni

Le validazioni principali sono:

- `dimensione_filtri`: formato `larghezzaxaltezza` con `x` minuscola, ad esempio `600x600`
- `frequenza_intervento`: numero + unità (`giorni`, `settimane`, `mesi`) oppure alias (`bimestrale`, `trimestrale`, `semestrale`, `annuale`)
- `quadro_elettrico`: univoco nella stessa linea
- campi obbligatori: non possono essere vuoti

Gli errori vengono mostrati con `InfoBar` nei dialoghi, senza chiudere il form.

## Dettaglio quadro e interventi

Aprendo una card si entra nel dettaglio del quadro. Il pannello mostra:

- quantità filtri
- dimensione
- frequenza intervento
- configurazione `in scadenza`
- ultimo intervento
- prossima scadenza
- giorni alla scadenza
- durata stato `in scadenza`
- data di inizio stato `in scadenza`
- stato corrente

È presente anche la tabella dello storico interventi, da cui si può:

- aggiungere un intervento
- modificare un intervento
- eliminare un intervento

Il ritorno alla griglia avviene con il pulsante indietro della navigazione.

## Report

La vista `Report` è pensata per il riepilogo operativo e per la stampa.

Stati disponibili:

- `Tutti`
- `In regola`
- `In scadenza`
- `Scaduti`

Il report aggiorna coerentemente:

- titolo
- conteggio quadri
- totale `Filtri da preparare`
- dettaglio per dimensione
- card mostrate

### Contenuto del report

Ogni card del report mostra:

- quadro elettrico
- dimensione
- quantità filtri
- ultimo intervento
- campo vuoto `Data nuovo intervento`

I risultati sono raggruppati con divisori per:

- `Reparto`
- `Linea`

### Stampa PDF

Il pulsante `Stampa` genera un PDF temporaneo e lo apre nel visualizzatore predefinito.

La versione stampabile:

- usa layout A4
- forza la white mode per leggibilità
- mantiene gli stessi raggruppamenti per reparto e linea

## Impostazioni

La vista `Impostazioni` permette di salvare preferenze persistenti in `data/app_preferences.json`.

Opzioni disponibili:

- tema: `Automatico`, `Chiaro`, `Scuro`
- lingua: `Sistema`, `Italiano`, `Inglese`
- formato data: `Sistema`, `gg/mm/aaaa`, `mm/gg/aaaa`

Note:

- il tema si applica subito
- il formato data si applica subito
- il cambio lingua richiede il riavvio dell'app

## Internazionalizzazione

L'app usa due livelli distinti:

- **Babel** per date e gestione cataloghi
- **gettext** a runtime per i testi compilati da cataloghi `.mo`

Cataloghi presenti:

- `backend/i18n/locales/it/LC_MESSAGES/filtri.po`
- `backend/i18n/locales/en/LC_MESSAGES/filtri.po`

Compilazione cataloghi:

```powershell
pybabel compile -d backend/i18n/locales -D filtri
```

I testi dell'app usano il wrapper `tr(...)`, così la UI non dipende direttamente dall'API `gettext`.

## Formato date e lingua sistema

La lingua dell'app viene determinata con priorità a:

1. preferenza utente salvata
2. lingue UI del sistema operativo
3. fallback italiano

Le date possono seguire:

- la lingua dell'app
- oppure una preferenza esplicita dell'utente

Esempi:

- italiano → `08/07/2026`
- inglese US → `07/08/2026`

## Configurazione stato `in scadenza`

La soglia di `in scadenza` ha due livelli di configurazione:

- **globale**, definita in `pyproject.toml`
- **personalizzata**, impostabile nel singolo quadro/filtro dalla sezione `Avanzate`

La configurazione globale di default usa i parametri in `pyproject.toml`:

```toml
[tool.filtri.stato]
preavviso_percentuale = 15
preavviso_massimo_giorni = 14
```

Esempi con la configurazione globale:

- frequenza `30 giorni` -> `in scadenza` negli ultimi 5 giorni
- frequenza `12 mesi` -> `in scadenza` negli ultimi 14 giorni

Nel dialogo di creazione o modifica del quadro, la sezione `Avanzate` permette di scegliere tra:

- `Valori globali`
- `Personalizzato`

Quando si seleziona `Personalizzato`, il filtro salva i propri valori di:

- percentuale `in scadenza`
- tetto massimo giorni

In questo modo due quadri diversi possono avere soglie `in scadenza` differenti, anche se la configurazione globale resta invariata.

I mesi usano aritmetica di calendario reale.

## Dati di esempio

`filtri-db seed --clear` popola il database con casi utili per testare:

- filtri `ok`
- filtri `warning`
- filtri `overdue`
- quadri senza interventi
- frequenze miste (`giorni`, `settimane`, `mesi`, alias periodici)

Questo permette di verificare rapidamente:

- badge stato
- dettaglio quadro
- logica report
- ricerca e filtri

## Struttura progetto

```text
filtri/
├── main.py
├── pyproject.toml
├── README.md
├── .env.example
├── data/
├── frontend/
│   ├── components/
│   │   ├── date_input.py
│   │   ├── filtro_card.py
│   │   ├── filtri_grid_panel.py
│   │   ├── hierarchy_dialogs.py
│   │   ├── hierarchy_tree.py
│   │   ├── multi_select_filter_button.py
│   │   ├── quadro_detail_panel.py
│   │   ├── scoped_search_line_edit.py
│   │   ├── select_setting_card.py
│   │   └── theme_aware_styles.py
│   └── views/
│       ├── home_view.py
│       ├── report_view.py
│       └── settings_view.py
└── backend/
    ├── config.py
    ├── settings.py
    ├── database/
    │   ├── alembic/
    │   ├── cli.py
    │   ├── db_manager.py
    │   ├── init_database.py
    │   ├── migrations.py
    │   └── seed.py
    ├── i18n/
    │   ├── __init__.py
    │   ├── dates.py
    │   ├── locale.py
    │   ├── translations.py
    │   └── locales/
    ├── models/
    ├── schemas/
    │   ├── app_preferences.py
    │   ├── filtri.py
    │   ├── hierarchy.py
    │   ├── settings.py
    │   └── stato_filtro.py
    └── services/
        ├── app_preferences_service.py
        ├── app_theme_service.py
        ├── filtri_service.py
        ├── hierarchy_crud_service.py
        ├── hierarchy_service.py
        ├── intervento_crud_service.py
        ├── preavviso_filtro_service.py
        └── stato_filtro_service.py
```

## Schema database

Relazione principale:

```text
sede -> reparto -> linea -> quadro_elettrico -> filtri -> interventi
```

Tabelle principali:

| Tabella | Contenuto |
|---------|-----------|
| `sede` | stabilimento / sede |
| `reparto` | reparti della sede |
| `linea` | linee del reparto |
| `quadro_elettrico` | quadri per linea |
| `filtri` | dati tecnici del filtro |
| `interventi` | storico interventi |

## Configurazione

### File principali

| File | Scopo |
|------|------|
| `pyproject.toml` | dipendenze, build, script e configurazioni app |
| `.env` | configurazione runtime locale |
| `data/app_preferences.json` | preferenze utente |

### Variabili `.env`

```env
# SQLite (default)
FILTRI_DATABASE_PATH=data/filtri.db

# Oppure URL completo
# FILTRI_DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/filtri
```

Priorità:

1. variabili d'ambiente di sistema
2. `.env`
3. valori di default nel codice

## Database e migrazioni

Uso normale:

- le migrazioni vengono applicate automaticamente all'avvio

Sviluppo:

```powershell
filtri-db revision --autogenerate -m "descrizione modifica"
filtri-db upgrade
```

Comandi principali:

| Comando | Descrizione |
|---------|-------------|
| `filtri` | avvia l'app |
| `filtri-db upgrade` | applica migrazioni |
| `filtri-db current` | versione corrente DB |
| `filtri-db downgrade` | annulla ultima migrazione |
| `filtri-db revision -m "..."` | crea migrazione |
| `filtri-db revision --autogenerate -m "..."` | genera migrazione dai modelli |
| `filtri-db seed` | popola il database |
| `filtri-db seed --clear` | reset + seed |
| `setup.bat` | installa o disinstalla il progetto su Windows |
| `start.bat` | avvia l'app su Windows usando la `.venv` |

## Dati di sviluppo

Le factory in `backend/factories/` usano **Factory Boy** e sono allineate al modello attuale.

Esempio:

```python
from backend.factories import SedeFactory, FiltroFactory

sede = SedeFactory(sede="Stabilimento Roma")
filtro = FiltroFactory(
    quantita_filtri=4,
    dimensione_filtri="600x600",
    frequenza_intervento="12 mesi",
)
```

## Audit e security

Per i controlli sulle dipendenze:

```powershell
pip install -e ".[audit]"
pip-audit
```

Con `setup.bat`:

```powershell
.\setup.bat
# poi scegli: audit
```

`pip-audit` controlla le CVE note nelle dipendenze pubbliche installate. È normale che il pacchetto locale del progetto possa comparire come non auditabile perché non pubblicato su PyPI.

Per analisi di sicurezza del codice:

```powershell
pip install -e ".[security]"
bandit -r backend frontend main.py
semgrep --config=auto backend frontend main.py
```

Con `setup.bat`:

```powershell
.\setup.bat
# poi scegli: security
```

Se vuoi entrambi:

```powershell
pip install -e ".[audit,security]"
```

Oppure dal menu di `setup.bat` inserisci:

```text
audit,security
```

Comandi utili dopo l'installazione:

```powershell
pip-audit
bandit -r backend frontend main.py
semgrep --config=auto backend frontend main.py
```

## Quality checks

Per controlli di qualita` e tipizzazione statica:

```powershell
pip install -e ".[quality]"
ruff check .
mypy
```

Con `setup.bat`:

```powershell
.\setup.bat
# poi scegli: quality
```

Se vuoi tutto insieme:

```powershell
pip install -e ".[audit,security,quality]"
```

Lo script `audit_security.bat` supporta ora anche:

```powershell
.\audit_security.bat quality
.\audit_security.bat all
```

`mypy` usa la configurazione definita in `pyproject.toml`, cosi` da partire con controlli piu` utili e meno rumorosi sulle aree gia` tipizzate meglio del progetto.

## Stack tecnologico

| Tecnologia | Ruolo |
|------------|-------|
| PySide6 | GUI desktop |
| PySide6-Fluent-Widgets | componenti Fluent Design |
| SQLAlchemy | ORM |
| Alembic | migrazioni DB |
| Pydantic | validazione dati |
| pydantic-settings | config da `.env` |
| Babel | date, cataloghi e tooling i18n |
| gettext | traduzioni runtime |
| Factory Boy | dati di sviluppo |
| SQLite | database predefinito |

## Sviluppo

```powershell
copy .env.example .env
pip install -e ".[dev]"
filtri-db upgrade
filtri-db seed --clear
filtri
```

File ignorati da git:

- `.venv/`
- `data/`
- `.env`
- `__pycache__/`
- `*.egg-info/`
- `dist/`
