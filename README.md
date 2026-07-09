# Gestionale Filtri

Applicazione desktop per la gestione di filtri industriali con interfaccia **PySide6 + Fluent Design**, database relazionale e report stampabili.

## Panoramica

L'app è organizzata in quattro aree principali:

- `Home`: dashboard con riepilogo rapido dei filtri
- `Filtri`: gestione operativa di gerarchia, ricerca, card filtro e dettaglio quadro
- `Report`: riepilogo filtrabile e stampabile dei quadri per stato
- `Impostazioni`: preferenze di tema, lingua e formato date

Funzionalità già disponibili:

- gerarchia `sede -> reparto -> impianto -> quadro elettrico`
- creazione, modifica, eliminazione e spostamento dei nodi della gerarchia
- creazione del quadro insieme al relativo filtro
- card filtro responsive con badge stato
- ricerca testuale con selezione dell'ambito
- filtro multiplo per stato
- dettaglio quadro con storico interventi
- report con stampa PDF
- localizzazione **italiano / inglese**
- rilevamento lingua del sistema operativo
- preferenze persistenti per tema, lingua, formato data e auto-refresh

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

`setup.bat` crea la `.venv` se manca, prova ad aggiornare `pip`, installa il progetto e crea `.env` da `.env.example` se necessario.

Se l'aggiornamento di `pip` non riesce, lo script mostra un avviso e continua comunque con l'installazione usando la versione già presente nella `.venv`.

Menu principale:

- `Installa / aggiorna l'app`
- `Disinstalla il pacchetto dalla .venv`
- `Factory reset repo`
- `Esci`

Nel sottomenu installazione i profili sono numerati:

- `1` = `standard`
- `2` = `dev`
- `3` = `audit`
- `4` = `security`
- `5` = `quality`
- `6` = `Indietro`
- `7` = `Esci`
- `8` = `all`

Sono supportate anche combinazioni multiple con input numerico, per esempio:

- `2,3`
- `2,4`
- `2,5`
- `3,4`
- `2,3,4`
- `2,3,4,5`
- `8`

Esempi:

```powershell
.\setup.bat
.\setup.bat install
.\setup.bat install 2
.\setup.bat install 3
.\setup.bat install 4
.\setup.bat install 5
.\setup.bat install 2,5
.\setup.bat install 8
.\setup.bat uninstall
```

`Factory reset repo` usa Git per riportare il repository a uno stato pulito del commit corrente, inclusa la rimozione dei file ignorati. Ha senso solo se il progetto è già sotto versionamento Git.

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

Serve come colpo d'occhio iniziale sullo stato generale dei quadri e dei filtri.

## Vista Filtri

La vista `Filtri` è divisa in due pannelli:

- a sinistra: contenuto operativo
- a destra: albero gerarchico della struttura

La TreeView rappresenta:

```text
sede -> reparto -> impianto -> quadro elettrico
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
- selezione di `sede`, `reparto` o `impianto`: griglia di card filtro
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
- `impianto`
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

Quando si crea un quadro da un `impianto`, il dialogo raccoglie:

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
- `quadro_elettrico`: univoco nello stesso impianto
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
- `Impianto`

### Stampa PDF

Il pulsante `Stampa` genera un PDF temporaneo e lo apre nel visualizzatore predefinito.

La versione stampabile:

- usa layout A4
- forza la white mode per leggibilità
- mantiene gli stessi raggruppamenti per reparto e impianto

## Impostazioni

La vista `Impostazioni` permette di salvare preferenze persistenti in `data/app_preferences.json`.

Opzioni disponibili:

- tema: `Automatico`, `Chiaro`, `Scuro`
- lingua: `Sistema`, `Italiano`, `Inglese`
- formato data: `Sistema`, `gg/mm/aaaa`, `mm/gg/aaaa`
- aggiornamento automatico: `15 secondi`, `30 secondi`, `1 minuto`, `5 minuti`

Note:

- il tema si applica subito
- il formato data si applica subito
- l'intervallo di aggiornamento automatico si applica subito
- il cambio lingua richiede il riavvio dell'app

L'app aggiorna inoltre dashboard, report e vista filtri in tempo reale quando cambiano i dati principali, come interventi o struttura gerarchica.

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
├── main.py                              # Punto di ingresso dell'app desktop
├── pyproject.toml                       # Dipendenze, script e configurazioni tool
├── README.md                            # Documentazione del progetto
├── .env.example                         # Esempio configurazione ambiente
├── setup.bat                            # Installazione guidata Windows
├── start.bat                            # Avvio rapido Windows
├── audit_security.bat                   # Controlli audit, security e quality
├── data/                                # Dati runtime locali (DB, preferenze)
├── frontend/                            # Interfaccia utente PySide6
│   ├── components/                      # Widget e pannelli riutilizzabili
│   │   ├── date_input.py                # Input data con parsing/formattazione utente
│   │   ├── frequenza_input.py           # Input guidato per frequenza intervento
│   │   ├── filtro_card.py               # Card singola riepilogo filtro
│   │   ├── filtri_grid_panel.py         # Griglia filtri e dettaglio quadro
│   │   ├── hierarchy_dialogs.py         # Dialog creazione/modifica/spostamento
│   │   ├── hierarchy_tree.py            # TreeView struttura sede/reparto/impianto
│   │   ├── intervento_dialog.py         # Dialog inserimento/modifica intervento
│   │   ├── multi_select_filter_button.py # Filtro multi-selezione stati
│   │   ├── preavviso_advanced_section.py # Sezione avanzata stato in scadenza
│   │   ├── quadro_detail_panel.py       # Dettaglio quadro e storico interventi
│   │   ├── scoped_search_line_edit.py   # Ricerca con ambiti selezionabili
│   │   ├── section_divider.py           # Separatore visivo sezioni
│   │   ├── select_setting_card.py       # Card impostazione con combo
│   │   └── theme_aware_styles.py        # Stili reattivi al tema corrente
│   └── views/                           # Pagine principali dell'app
│       ├── dashboard_view.py            # Dashboard Home con riepilogo stati
│       ├── filtri_view.py               # Pagina operativa filtri e struttura
│       ├── home_view.py                 # Finestra principale e navigazione
│       ├── report_view.py               # Report filtrabile e stampabile
│       └── settings_view.py             # Impostazioni tema, lingua, date, refresh
└── backend/                             # Logica applicativa e accesso dati
    ├── config.py                        # Config ad alto livello dell'app
    ├── settings.py                      # Lettura configurazione runtime / .env
    ├── database/                        # Gestione database e migrazioni
    │   ├── alembic/                     # Ambiente e versioni Alembic
    │   ├── cli.py                       # Comandi CLI filtri-db
    │   ├── db_manager.py                # Engine, sessioni e URL database
    │   ├── init_database.py             # Bootstrap database all'avvio
    │   ├── migrations.py                # Wrapper esecuzione migrazioni
    │   └── seed.py                      # Popolamento dati di esempio
    ├── i18n/                            # Localizzazione e traduzioni
    │   ├── __init__.py                  # API i18n esposta al resto dell'app
    │   ├── dates.py                     # Parsing e formato date localizzato
    │   ├── locale.py                    # Risoluzione lingua/locale attivo
    │   ├── translations.py              # Wrapper gettext e titoli report
    │   └── locales/                     # Cataloghi .po/.mo italiano e inglese
    ├── models/                          # Modelli ORM SQLAlchemy
    │   ├── base.py                      # Base dichiarativa comune
    │   ├── sede.py                      # Modello sede
    │   ├── reparto.py                   # Modello reparto
    │   ├── impianto.py                  # Modello impianto
    │   ├── quadro_elettrico.py          # Modello quadro elettrico
    │   ├── filtro.py                    # Modello filtro
    │   ├── intervento.py                # Modello intervento
    │   └── __init__.py                  # Export centralizzati modelli
    ├── schemas/                         # Schemi Pydantic e DTO applicativi
    │   ├── app_preferences.py           # Preferenze utente persistenti
    │   ├── filtri.py                    # DTO card, dettagli e report filtri
    │   ├── frequenza.py                 # Normalizzazione frequenze intervento
    │   ├── hierarchy.py                 # Schemi gerarchia e CRUD nodi
    │   ├── settings.py                  # Costanti percorso e root progetto
    │   ├── stato_filtro.py              # Tipi e config per stato filtro
    │   └── __init__.py                  # Package schemas
    └── services/                        # Servizi di business logic
        ├── app_preferences_service.py   # Caricamento/salvataggio preferenze
        ├── app_theme_service.py         # Applicazione tema e preferenze UI
        ├── filtri_service.py            # Query filtri, dashboard e report
        ├── hierarchy_crud_service.py    # CRUD e move sulla gerarchia
        ├── hierarchy_service.py         # Caricamento struttura ad albero
        ├── intervento_crud_service.py   # CRUD interventi
        ├── preavviso_filtro_service.py  # Calcolo descrizione e config preavviso
        └── stato_filtro_service.py      # Calcolo stati e scadenze filtro
```

## Schema database

Relazione principale:

```text
sede -> reparto -> impianto -> quadro_elettrico -> filtri -> interventi
```

Tabelle principali:

| Tabella | Contenuto |
|---------|-----------|
| `sede` | stabilimento / sede |
| `reparto` | reparti della sede |
| `impianto` | impianti del reparto |
| `quadro_elettrico` | quadri per impianto |
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
