import click 
import sqlite3
import os

@click.group(invoke_without_command=True)
@click.pass_context
@click.argument('database', type=click.Path(exists=True))
def cli(ctx, database):
    """
    A less-like interface for exploring SQLite schema and table data. If invoked without a COMMAND on a DATABASE, stats about the DATABASE are displayed.
    """
    ctx.ensure_object(dict)
    ctx.obj['abort'] = True
    conn = sqlite3.connect(database)
    if ctx.invoked_subcommand is None:
        # fetch and display db stats
        stats = {}
        conn.row_factory = sqlite3.Row
        with conn:
            stats['tables'] = conn.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\'table\'').fetchone()[0]
            stats['indexes'] = conn.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\'index\'').fetchone()[0]
            stats['views'] = conn.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\'view\'').fetchone()[0]
            stats['triggers'] = conn.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\'trigger\'').fetchone()[0]
            stats['size'] = os.path.getsize(database)
        click.secho(f'Database Stats: {database}', bold=True)
        click.secho('+ File Size: ', nl=False)
        click.secho(f'{stats["size"]:,d} bytes', bold=True)
        click.secho('+ Number of Tables: ', nl=False)
        click.secho(f'{stats["tables"]:,d}', bold=True)
        click.secho('+ Number of Indexes: ', nl=False)
        click.secho(f'{stats["indexes"]:,d}', bold=True)
        click.secho('+ Number of Views: ', nl=False)
        click.secho(f'{stats["views"]:,d}', bold=True)
        click.secho('+ Number of Triggers: ', nl=False)
        click.secho(f'{stats["triggers"]:,d}', bold=True)
    else:
        # prepare context for subcommand
        ctx.obj['abort'] = False
        ctx.obj['db'] = database
    conn.close()

@click.command()
@click.pass_context
def schema(ctx):
    """
    View an SQLite DATABASE's schema.
    """
    if not(ctx.obj['abort']):
        sg = schema_generator(ctx.obj['db'])
        click.echo_via_pager(sg)

@click.command()
@click.pass_context
@click.argument('tablename', nargs=-1)
@click.option('--stats', '-s', is_flag=True, help='Instead of paging through actual rows of DATABASE tables, provide stats for each table.')
@click.option('--range', '-r', '_range', multiple=True, nargs=3, type=(str, int, int), help='This option may be used multiple times and takes three arguments each time it is used: the name of a table, the lower row limit, and the upper row limit. For example, "--range customer 50 100" indicates you are only interested in records 50 (inclusive) through 100 (inclusive) in the customers table. In the absence of this option, all records in a table will be displayed. In any case, table records will not be displayed if: the table name is not also passed as an argument, or the default argument of all tables is used. If the upper limit is lower than the lower limit, your upper limit will be ignored and records through the end if the table will be displayed.')
@click.option('--chunk', '-c', default=10, help='The number of rows to select at a time from the database\'s table(s) to power the pager. The default value is 10. Passing a 0 indicates to pull an entire table at once into memory.')
@click.option('--truncate', '-t', default=0, help='The maximum number of characters to print for any field in any row pulled from the database. The default value of 0 indicates that no truncating should occur.')
@click.option('--orderby', '-o', 'order', multiple=True, nargs=3, type=(str, str, str), help='Specify a table, column, and ASC or DESC to order the result set of rows fed into the pager accordingly. You may use one --orderby option for each table you are targeting. You must pass the name of a column that exists in the database table you are targeting, or the program will enter an error state.')
def tables(ctx, tablename, stats, _range, chunk, truncate, order):
    """
    Explore the data in an SQLite DATABASE. If one or more TABLENAMEs are provided, it is used as a whitelist of tables to print records from, otherwise all tables will be drawn from.
    """
    if not(ctx.obj['abort']):
        lg = None
        if len(tablename) < 1:
            conn = sqlite3.connect(ctx.obj['db'])
            with conn:
                tablename = conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()
                tablename = [t[0] for t in tablename]
            conn.close()
        if stats:
            sg = stats_generator(ctx.obj['db'], tablename)
            lg = line_generator(sg)
        else:
            tg = tables_generator(ctx.obj['db'], tablename, _range, chunk, truncate, order)
            lg = line_generator(tg)
        click.echo_via_pager(lg)

cli.add_command(schema)
cli.add_command(tables)

def schema_generator(database):
    conn = sqlite3.connect(database)
    with conn:
        tables = conn.execute('SELECT name FROM sqlite_master WHERE type=\'table\'').fetchall()
        for t in tables:
            cols = conn.execute(f'PRAGMA table_info({t[0]})').fetchall()
            yield f'\nTABLE {t[0]}:\n\n'
            for c in cols:
                yield f'Column {c[0]}:\n'
                yield f'+ Name: {c[1]}\n'
                yield f'+ Type: {c[2]}\n'
                yield f'+ Nullable: {"True" if not(c[3]) else "False"}\n'
                yield f'+ Default Value: {"None" if c[4] is None else c[4]}\n'
                yield f'+ Primary Key: {"True" if c[5] else "False"}\n'
            yield '\n\n'
    conn.close()

def tables_generator(database, tables, _range, chunk, truncate, order):
    _range = get_range_dict(_range)
    order = get_order_dict(order)
    if truncate < 0:
        truncate = 0
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    with conn:
        for t in tables:
            if t not in _range.keys():
                _range[t] = {}
                _range[t]['l'] = 0
                _range[t]['u'] = -1
            if t not in order.keys():
                order[t] = []
            yield f'***\nTABLE {t}:\n***\n\n'
            order_segs = []
            with open('sql2.log', 'w') as f:
                f.write('\n')
            for i,v in enumerate(order[t]):
                if i == 0:
                    order_segs.append(' ORDER BY ')
                order_segs.append(v[0])
                order_segs.append(' ')
                order_segs.append(v[1])
                if i != len(order[t]) - 1:
                    order_segs.append(', ')
            if chunk < 1:
                offset = _range[t]['l'] - 1
                limit  = _range[t]['u'] - _range[t]['l'] + 1
                q = f"SELECT * FROM {t}{''.join(order_segs)} LIMIT {limit if limit > 0 else -1} OFFSET {offset}"
                with open('sql2.log', 'a') as f:
                    f.write(q)
                    f.write('\n')
                results = conn.execute(q).fetchall()
                for row in results:
                    for k in row.keys():
                        yield f'***\nField {k}:\n***\n'
                        yield f'{row[k]}\n' if not(truncate) else f'{str(row[k])[:truncate]}'
                    yield '\n'
            else:
                read_count = 0
                total_limit = _range[t]['u'] - _range[t]['l'] + 1
                if total_limit < 1:
                    total_limit = float('inf')
                offset = _range[t]['l'] - 1
                while read_count <= total_limit:
                    limit = None
                    if read_count > 0:
                        offset += chunk 
                    if read_count + chunk <= total_limit:
                        limit = chunk
                    else:
                        limit = total_limit - read_count
                    if limit < 1:
                        break
                    read_count += limit
                    q = f'SELECT * FROM {t}{"".join(order_segs)} LIMIT {limit} OFFSET {offset}'
                    records = conn.execute(q).fetchall()
                    if len(records) < 1:
                        break
                    else: 
                        for r in records:
                            for k in r.keys():
                                yield f'***\nField {k}:\n***\n'
                                yield f'{r[k]}\n' if not(truncate) else f'{str(r[k])[:truncate]}'
                            yield '\n'
            yield '\n'
    conn.close()

def stats_generator(database, tables):
    conn = sqlite3.connect(database)
    with conn:
        for t in tables:
            yield f'Table Stats: {t}\n'
            c = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            yield f'+ Number of Rows: {c}\n'
            i = conn.execute(f'SELECT COUNT(*) FROM sqlite_master WHERE type=\'index\' AND tbl_name=\'{t}\'').fetchone()[0]
            yield f'+ Number of Indexes: {i}\n'
            yield '\n'
    conn.close()

def line_generator(generator):
    while True:
        try:
            yield next(generator)
        except StopIteration:
            break

def get_range_dict(ranges):
    o = {}
    for r in ranges:
        o[r[0]] = {}
        if r[1] < 0:
            o[r[0]]['l'] = 0
        else:
            o[r[0]]['l'] = r[1]
        if r[2] < r[1]:
            o[r[0]]['u'] = -1
        else:
            o[r[0]]['u'] = r[2]
    return o

def get_order_dict(orders):
    o = {}
    for r in orders:
        if r[0] not in o.keys():
            o[r[0]] = []
        curr = []
        curr.append(r[1])
        if r[2].upper() == 'ASC':
            curr.append('ASC')
        else:
            curr.append('DESC')
        o[r[0]].append(curr)
    return o







