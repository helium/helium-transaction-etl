from follower import Follower
import argparse
from models.migrations import Base
from models.migrations import detailed_receipts_sql
from sqlalchemy.engine import create_engine
import os
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser()

    parser.add_argument("--migrate", action="store_true", help="Creates tables if they do not already exist.")
    parser.add_argument("--start", action="store_true", help="Starts the ETL.")

    args = parser.parse_args()

    if args.migrate:
        print("Running migrations...")
        engine = create_engine(os.getenv("POSTGRES_CONNECTION_STR"))
        Base.metadata.create_all(engine)
        engine.execute(detailed_receipts_sql)
        print("done.")

    if args.start:
        follower = Follower()
        follower.run()

