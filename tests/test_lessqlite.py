import sqlite3
from lessqlite import __version__, cli
from dbml_sqlite import toSQLite
from faker import Faker
from click.testing import CliRunner

fake = Faker()

dbml = """
table one {
    id integer PK
    name text
}

table two {
    id integer PK
    place text
}
"""

def test_version():
    assert __version__ == '0.1.4'

def test_cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('a.dbml', 'w') as a:
            a.write(dbml)
        ddl = toSQLite('a.dbml')
        conn = sqlite3.connect('test.db')
        with conn:
            conn.executescript(ddl)
        with conn:
            for _ in range(500):
                conn.execute(f'INSERT INTO one (name) VALUES (\'{fake.name()}\')')
                conn.execute(f'INSERT INTO two (place) VALUES (\'{fake.address()}\')')
        conn.close()
        result = runner.invoke(cli, ['test.db'])
        assert 'Number of Tables: 2' in result.output
        assert 'Database Stats: test.db' in result.output
        result = runner.invoke(cli, ['test.db', 'schema'])
        assert 'Column 1' in result.output
        assert 'TABLE one' in result.output 
        result = runner.invoke(cli, ['test.db', 'tables', '--stats'])
        assert 'Table Stats: one\n' in result.output 
        assert 'Table Stats: two\n' in result.output 
        assert 'Number of Rows: 500\n' in result.output
        result = runner.invoke(cli, ['test.db', 'tables', 'one', '--chunk', '10'])
        assert 'TABLE one' in result.output 
        assert 'TABLE two' not in result.output 
        result = runner.invoke(cli, ['test.db', 'tables', 'one', '--truncate', '-1', '--range', 'one', '-1', '15', '--chunk', '10'])
        assert 'TABLE one' in result.output
        result = runner.invoke(cli, ['test.db', 'tables', '--range', 'one', '2', '-1'])
        assert 'TABLE two' in result.output
        result = runner.invoke(cli, ['test.db', 'tables', '--range', 'one', '1', '10', '--orderby', 'one', 'id', 'desc', '--orderby', 'one', 'name', 'asc'])
        assert '499' in result.output
        result = runner.invoke(cli, ['test.db', 'tables', '--range', 'one', '2', '11', '--chunk', '0'])
        assert '2' in result.output 
