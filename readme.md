# Virma ← LIPAS integration

Continuous importer that mirrors [LIPAS](https://lipas.fi/) sports place data into the
[Virma](https://virma.fi/) database, so that Virma can show up-to-date points and routes.
The data is enriched with annotations that are maintained in the database.

The other direction (Virma → LIPAS) is handled by
[digiretki_to_lipas](https://github.com/Lounaispaikka/digiretki_to_lipas).

## How it works

- Every night the importer downloads the LIPAS sports places that have been modified
  since the previous run and upserts them into the `lipas` table.
- The classification of a place (`class1_fi`, `class2_fi`) is kept in the
  `lipas_annotations` table and is guessed from the classifications of the other
  places of the same LIPAS type.
- An administrator reviews and corrects the classifications, see
  [ohjeistus.md](ohjeistus.md) (in Finnish).
- Places that have been removed in LIPAS are deleted from the database.

## Requirements

- Python 3.12 or newer (developed and tested with 3.15)
- PostgreSQL with PostGIS
- A LIPAS API key is not needed, the importer uses the public API

## Development

Dependencies are managed with [uv](https://docs.astral.sh/uv/).

```shell
uv sync                 # create .venv and install the locked dependencies
cp lipas_virma_importer/config_example.py lipas_virma_importer/config.py
uv run python -m lipas_virma_importer   # run the importer
uv run alembic upgrade head              # run database migrations
uv run lipas-virma-importer              # console script, same as above
```

`uv.lock` is committed, so use `uv sync --locked` (or `--frozen`) to install
exactly the locked versions, e.g. in CI or Docker. Update the lock with
`uv lock` (and `uv lock --upgrade` to also refresh the pinned versions).

The database connection is read from `lipas_virma_importer/config.py`, which is
not tracked in git. See `config_example.py` for the available options.

## Production

The importer runs as a nightly cron job. Prepare the environment once:

```shell
cd /home/lipas/virma_lipas
uv sync --locked
```

and run it with (the environment is not synced again, the lockfile is not
updated):

```cron
0 2 * * * (cd /home/lipas/virma_lipas && /usr/bin/flock -n /home/lipas/lipas_virma_importer.lock uv run --frozen --no-sync python -m lipas_virma_importer 2>&1) 2>>/home/lipas/err.log >>/home/lipas/log.log
```

## Docker

```shell
docker build -t lipas-virma-importer .
docker run --rm -v $PWD/lipas_virma_importer/config.py:/app/lipas_virma_importer/config.py lipas-virma-importer
```

## License

MIT — see [LICENSE.md](LICENSE.md).

## Acknowledgements

Code artifacts produced as part of the [Digiretki](https://tt.utu.fi/sweng/digiretki/) project. Co-funded by the European Union.

*We thank the Lipas staff for their invaluable help in forming this solution. We also thank Metsähallitus for their guidance and support in progressing the project and this solution to the right direction!*

<img width="1536" height="343" alt="EU logo" src="https://github.com/user-attachments/assets/9bf00b51-c1d7-4384-8b4b-1d66ff1f88bd" />
