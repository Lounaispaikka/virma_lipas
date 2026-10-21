# Virma ← LIPAS integration

Continuous importer that mirrors [LIPAS](https://lipas.fi/) sports place data into the
[Virma](https://virma.fi/) database, so that Virma can show up-to-date points and routes.
The data is enriched with annotations that are maintained in the database.

The other direction (Virma → LIPAS) is handled by
[digiretki_to_lipas](https://github.com/Lounaispaikka/digiretki_to_lipas).

## Suomeksi

Automaatio, joka kopioi [Lipas](https://lipas.fi/) -palvelun liikuntapaikka-aineiston
[Virman](https://virma.fi/) tietokantaan, jotta Virma pystyy näyttämään ajantasaiset
pisteet ja reitit. Kohteiden luokittelu (`class1_fi`, `class2_fi`) ja ylläpitäjän tekemät
muutokset säilytetään tietokannassa.

Käyttöohjeet ylläpitäjälle: [ohjeistus.md](ohjeistus.md).

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
cp .env.example .env                        # and edit the database credentials
uv run alembic upgrade head              # run database migrations
uv run lipas-virma-importer              # console script, same as above
```


The settings are read from the environment. For development they can be kept in
a `.env` file in the project root, which is not tracked in git. See
`.env.example` for the available options.

### The views are not refreshed by the importer

The importer only writes to the `lipas`, `lipas_annotations` and `lipas_config`
tables. The data that the Virma application reads comes from the
`routes_combined` and `points_combined` views, which are materialized views in
the production database. **Nothing in this repository refreshes them** — the
production database refreshes them about once an hour, so the data shown in the
user interface can lag behind the imported data.

A developer can refresh them manually:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY routes_combined;
REFRESH MATERIALIZED VIEW CONCURRENTLY points_combined;
```

`database_custom_rules.sql` creates the two views as plain views, so in a
development database there is nothing to refresh and the views always show the
current data.

## Production

The importer runs as a nightly cron job. Prepare the environment once:

```shell
cd /home/lipas/virma_lipas
uv sync --locked
cp .env.example .env                       # and edit the database credentials
```

and run it with (the environment is not synced again, the lockfile is not
updated):

```cron
0 2 * * * (cd /home/lipas/virma_lipas && /usr/bin/flock -n /home/lipas/lipas_virma_importer.lock uv run --frozen --no-sync python -m lipas_virma_importer 2>&1) 2>>/home/lipas/err.log >>/home/lipas/log.log
```

## Docker

```shell
docker build -t lipas-virma-importer .
docker run --rm --env-file .env lipas-virma-importer
```

The database must be reachable from the container, so `DB_HOST` cannot be
`127.0.0.1` unless the container shares the network with the host
(`docker run --network host`).

## License

MIT — see [LICENSE.md](LICENSE.md).

## Acknowledgements

The project was modified during the [Digiretki](https://tt.utu.fi/sweng/digiretki/) project. Co-funded by the European Union.

<img width="1536" height="343" alt="EU logo" src="https://github.com/user-attachments/assets/9bf00b51-c1d7-4384-8b4b-1d66ff1f88bd" />
