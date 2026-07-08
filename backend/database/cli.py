"""CLI per le migrazioni del database."""

import argparse
import sys

from backend.database.migrations import (
    create_revision,
    current_revision,
    downgrade_database,
    upgrade_database,
)
from backend.database.seed import seed_dev_data


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="filtri-db",
        description="Gestione migrazioni database",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("upgrade", help="Applica tutte le migrazioni pendenti")
    subparsers.add_parser("current", help="Mostra la versione corrente del database")

    downgrade_parser = subparsers.add_parser("downgrade", help="Annulla migrazioni")
    downgrade_parser.add_argument(
        "revision",
        nargs="?",
        default="-1",
        help="Revisione di destinazione (default: -1)",
    )

    revision_parser = subparsers.add_parser("revision", help="Crea una nuova migrazione")
    revision_parser.add_argument("-m", "--message", required=True, help="Descrizione della migrazione")
    revision_parser.add_argument(
        "--autogenerate",
        action="store_true",
        help="Genera automaticamente le modifiche dai modelli",
    )

    seed_parser = subparsers.add_parser("seed", help="Popola il database con dati di esempio")
    seed_parser.add_argument(
        "--clear",
        action="store_true",
        help="Svuota il database prima di inserire i dati",
    )

    args = parser.parse_args(argv)

    if args.command == "upgrade":
        upgrade_database()
    elif args.command == "current":
        current_revision()
    elif args.command == "downgrade":
        downgrade_database(args.revision)
    elif args.command == "revision":
        create_revision(args.message, autogenerate=args.autogenerate)
    elif args.command == "seed":
        seed_dev_data(clear=args.clear)


if __name__ == "__main__":
    main(sys.argv[1:])
