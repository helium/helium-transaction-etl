# helium-transaction-etl
Lightweight ETL to store (primarily) challenge receipt data 

## Quickstart (Ubuntu)
* Follow these instructions to run the latest version of [`blockchain-node`](https://github.com/helium/blockchain-node).
    * **NOTE**: You *may* want to make changes to the node configuration in [`config/sys.config`](https://github.com/helium/blockchain-node/blob/master/config/sys.config), namely:
      * Change `store_json` parameter from `false` to `true`
      * Change `fetch_latest_from_snap_source` from `true` to `false`. You can then put a valid snapshot height in `blessed_snapshot_height` if you would like your node to load some historical data. However, bear in mind that the further back you go, the more difficult it is to find a peer with the snap, and the longer it will take to sync.

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


## Limitations

**At this point, the service ONLY populates the `challenge_receipts_parsed` and `payments_parsed` tables. `gateway_inventory` is refreshed daily via a bulk download from [DeWi ETL Data Dumps](https://dewi-etl-data-dumps.herokuapp.com/).**



