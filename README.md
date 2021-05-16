# *lessqlite*

![lessqlite](https://github.com/dvanderweele/lessqlite/actions/workflows/test.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/dvanderweele/lessqlite/badge.svg?branch=main)](https://coveralls.io/github/dvanderweele/lessqlite?branch=main)

*v0.1.1*

`lessqlite` is a free command-line utility written in Python providing a pager-based interface (like Unix `less`) for exploring, browsing, and scrolling through SQLite databases in your terminal. 

The program is powered by generator functions so that even SQLite databases of very large sizes can be paged through easily.

If you do anything interesting with this library, shoot me a link and I can feature it in this README.

## Installation

If you install `lessqlite` globally on your system via pip, you should be able to use it from anywhere:

```
pip install lessqlite
```

Of course you can install it in a virtual environment as well for a project.

## Usage

There are several different ways to use the tool so that you can customize your browsing experience. 

A good place to start is the root help page:

```
lessqlite --help
```

or

```
lessqlite -h
```

### Stats 

If you aren't viewing the root help page (see previous section), you must provide a path to a valid SQLite database as an argument:

```
lessqlite example.db
```

Such an invocation *will not* provide a pager interface for the database. Instead, it will print out a few simple statistics about your database.

### Schema

The first subcommand is `schema`, and as its name suggests it allows you to browse the provided database's schema of tables and columns in a pager-based interface. 

For example:

```
lessqlite example.db schema
```

This subcommand has its own help page:

```
lessqlite example.db schema --help 
```

### Tables

The `tables` subcommand is designed to be configurable enough to give you a comfortably flexible experience with browsing through an SQLite database in a terminal.

If you forget how the options work or if you want to see the short versions of the flags we will cover next, check the help page:

```
lessqlite example.db tables --help
```

#### TABLENAME Arguments

The `tables` subcommand accepts a variable number of arguments in the form of table names (0+). If no table names are provided as arguments, then all tables will be browsed instead. 

The following command will allow you to scroll through all records in all tables:

```
lessqlite example.db tables 
```

Providing one or more table names as arguments functions as a kind of whitelist of tables to page through. 

In the following example, only the `student` and `instructor` tables will be paged through:

```
lessqlite example.db tables student instructor 
```

#### Chunking

By default, the contents of each table will be selected in chunks of at most 10 records at a time from the database for feeding into the pager. It is possible to configure the chunk size with the option `--chunk`. 

The following example will chunk the records 50 at a time:

```
lessqlite example.db tables --chunk 50
```

To not chunk at all and instead pull each table into memory at once, pass 0 to the chunk option. Just be careful. For exceptionally large databases, this can be memory inefficient — or even memory impossible. 

#### Table Stats

To help you decide how to explore one or more tables, you can pass the `--stats` option, and the row count as well as other stats eill be displayed in the pager (rather than the actual rows of data). 

In the following example, only stats will be displayed about the two named tables:

```
lessqlite example.db tables student instructor --stats 
```

#### Truncating Fields

Another option to configure your experience of using the pager is the `--truncate` option. Pass a positive integer to it, and any field in any row with data of length surpassing the truncate option will be truncated to that length. 

In the following example, all outputted fields in all rows of the specified table will have a max output length of 300 characters:

```
lessqlite example.db tables blog_post --truncate 300
```

#### Ranges of Records

By default, the pager will page through all records in each targeted table. For tables with lots of records, this may be more than you are really interested in. 

You can specify at most one range of records for each table you'll be paging through. Each usage of the `--range` option takes exactly three arguments: the name of the table that the range applies to, an integer referring to the lower limit (inclusive) for records to be displayed, and an integer referring to the upper limit (inclusive) for records to be displayed. 

In this example, the 51st through 60th records of the result set will be displayed:

```
lessqlite example.db tables student --range 51 60
```

Note, 51 to 60 is *not* necessarily synonymous with records with ids 51 to 60. 

#### Ordering Records

The `--orderby` option takes three arguments: a table name, the name of a column in that table, and either ASC or DESC. This allows you to sort the result set of columns according to a particular column before they are fed into the pager.

You may specify this option multiple times, one or more times per table. If a particular table is targeted by more than one option, it will apply the orderings in the order you specified them.

For example, sort the student table records by last_name in ascending order and the instructor table by id in descending order:

```
lessqlite example.db tables student instructor --orderby student last_name asc --orderby instructor id desc 
```

According to my tests, it seems as though tables whose integer primary keys are an alias for the SQLite rowids (the most common type of SQLite table), in the absence of an explicit ordering, will tend to have their records selected in an ascending order according to those primary keys. 
