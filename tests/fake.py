import sqlite3
from dbml_sqlite import toSQLite
from faker import Faker

fake = Faker()

def main():
    ddl = toSQLite('a.dbml')
    conn = sqlite3.connect('test.db')
    with conn:
        conn.executescript(ddl)
    with conn:
        for _ in range(500):
            conn.execute(f'INSERT INTO one (name) VALUES (\'{fake.name()}\')')
            conn.execute(f'INSERT INTO two (address) VALUES (\'{fake.address()}\')')
    conn.close()
main()
