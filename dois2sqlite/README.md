## `dois2sqlite`

Tool for loading Crossref metadata into a SQLite database.

Includes example with a simple content-negotiation server.

You know, for fun.

**Installation**

- `python -m venv venv`
- `. ./venv/bin/activate`
- `pip install -e .` (`-e` assuming you might want to edit package)
- `pip install -e '.[dev]'` if you want to be able dev/edit code

**Usage**:

```console
$ dois2sqlite [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `create`: Create a new SQLite database at the...
- `index`: Create indexes on an existing SQLite...
- `load`: Load data from a src into SQLite.
- `tarinfo`: Analyze the TAR file and print out...

## `dois2sqlite create`

Create a new SQLite database at the specified path.

**Usage**:

```console
$ dois2sqlite create [OPTIONS] SQLITE_PATH
```

**Arguments**:

- `SQLITE_PATH`: [required]

**Options**:

- `--verbose / --no-verbose`: Verbose mode [default: no-verbose]
- `--help`: Show this message and exit.

## `dois2sqlite index`

Create indexes on an existing SQLite database.

**Usage**:

```console
$ dois2sqlite index [OPTIONS] SQLITE_PATH
```

**Arguments**:

- `SQLITE_PATH`: [required]

**Options**:

- `--verbose / --no-verbose`: Verbose mode [default: no-verbose]
- `--help`: Show this message and exit.

## `dois2sqlite load`

Load data from a src into SQLite.

**Usage**:

```console
$ dois2sqlite load [OPTIONS] SRC_PATH SQLITE_PATH
```

**Arguments**:

- `SRC_PATH`: [required]
- `SQLITE_PATH`: [required]

**Options**:

- `--n-jobs INTEGER`: Number of jobs [default: 1]
- `--commit-size INTEGER`: Number of records to commit at a time [default: 500000]
- `--verbose / --no-verbose`: Verbose mode [default: no-verbose]
- `--dry-run / --no-dry-run`: Dry run. Does everything except the actual insert into the database. [default: no-dry-run]
- `--max-files INTEGER`: Maximum number of files to process
- `--convert-to-commonmeta / --no-convert-to-commonmeta`: Convert to commonmeta [default: no-convert-to-commonmeta]
- `--clobber-sqlite / --no-clobber-sqlite`: Clobber the SQLite database, if it already exists [default: no-clobber-sqlite]
- `--help`: Show this message and exit.

## `dois2sqlite tarinfo`

Analyze the TAR file and print out information about it, including the following:

- The number of JSON files in the TAR file
- The estimated number of work items in total

**Usage**:

```console
$ dois2sqlite tarinfo [OPTIONS] TAR_PATH
```

**Arguments**:

- `TAR_PATH`: [required]

**Options**:

- `--verbose / --no-verbose`: Verbose mode [default: no-verbose]
- `--help`: Show this message and exit.
