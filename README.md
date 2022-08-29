# helium-transaction-etl
Lightweight ETL to store (primarily) challenge receipt data. 

## Quickstart (Ubuntu)
* Follow these instructions to run the latest version of [`blockchain-node`](https://github.com/helium/blockchain-node).
    * **NOTE**: You *may* want to make changes to the node configuration in [`config/sys.config`](https://github.com/helium/blockchain-node/blob/master/config/sys.config), namely:
      * Change `store_json` parameter from `false` to `true`
      * Change `fetch_latest_from_snap_source` from `true` to `false`. You can then put a valid snapshot height in `blessed_snapshot_height` if you would like your node to load some historical data. However, bear in mind that the further back you go, the more difficult it is to find a peer with the snap, and the longer it will take to sync.

* In terms of hardware recommendations, I run the node, database, and this ETL on a c5ad.2xlarge with some room to spare. Your RAM requirements will largely depend on how you index the database (see **Database Recommendations**).

* Make sure that you have a valid postgres database to connect to.

* Clone this repository and `cd` into the main directory
* Make a copy of `.env.template`, call it `.env`, and edit the environment variables with your settings. 
* Install dependencies with 

`pip install -r requirements.txt`

* Run the migrations to create the necessary tables

`python etl.py --migrate`

* Start the block follower

`python etl.py --start`

After backfilling all blocks stored on the node, the service will listen for new blocks and process them as they come in. 

## Database Recommendations

* I recommend installing `postgis` and the [`h3`](https://github.com/bytesandbrains/h3-pg) extensions on your postgres instance for additional functionality, such as distance calculations as kRing-based queries.
* Because the ETL deletes rows that are older than the `BLOCK_INVENTORY_SIZE` environment variable, certain tables - namely `challenge_receipts_parsed` - can get bogged down with a large number of dead tuples. I *strongly* recommend implementing a regular `VACUUM` operation to alleviate this issue. You can schedule the jobs using a tool like [`pg_cron`](https://www.citusdata.com/blog/2016/09/09/pgcron-run-periodic-jobs-in-postgres/).
* Within `challenge_receipts_parsed`, put indexes on `block`, `transmitter_address`, and `witness_address` columns for better performance on common queries.

## Limitations

**If you need deep historical records of the Helium ledger, use [blockchain-etl](https://github.com/helium/blockchain-etl) or the public API. This tool is best suited for short-term analyses (~5-10 days) of recent chain events.**

At this point, the service populates the following tables:
* `challenge_receipts_parsed`
* `payments_parsed`
* `gateway_inventory` (refreshed daily via a bulk download from [DeWi ETL Data Dumps](https://dewi-etl-data-dumps.herokuapp.com/))
* `denylist`

See [migrations.py](models/migrations.py) for the SQLAlchemy schema definitions.

## Docker

Build image with:

`make docker-build`

Then start it with:

`make docker-start`

To learn more: `make help`

## Related Projects

* [h3-countries](https://github.com/evandiewald/h3-countries): Postgres-based mapping of h3 indices to country codes.
* [dewi-alliance/hplans](https://github.com/dewi-alliance/hplans): Helium frequency plan regions in GeoJSON format.
* [dewi-alliance/helium-etl-lite](https://github.com/dewi-alliance/helium-etl-lite): A general-purpose light ETL for the Helium blockchain. 

