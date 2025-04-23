import argparse
from database import Base, engine, SessionLocal

def create_tables():
    with SessionLocal() as db:
        Base.metadata.create_all(bind=engine)

def drop_tables():
    with SessionLocal() as db:
        Base.metadata.drop_all(bind=engine)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage database tables")
    parser.add_argument("action", choices=["create", "drop"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "create":
        create_tables()
        print("Tables created")
    elif args.action == "drop":
        drop_tables()
        print("Tables dropped")
