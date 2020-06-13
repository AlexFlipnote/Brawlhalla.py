from utils import sqlite as db


class Accounts(db.Table):
    user_id = db.Column("BIGINT", nullable=False, primary_key=True)
    steamid64 = db.Column("BIGINT", nullable=False)
    brawlhalla_id = db.Column("INT", nullable=False)


def creation(debug: bool = False):
    """ Create tables or add missing columns to tables """
    failed = False

    for table in db.Table.all_tables():
        try:
            table.create()
        except Exception as e:
            print(f'Could not create {table.__tablename__}.\n\nError: {e}')
            failed = True
        else:
            if debug:
                print(f'[{table.__module__}] Created {table.__tablename__}.')

    # Return True if everything went as planned, else False
    return True if not failed else False
