## WORK IN PROGRESS PACKAGE

This repository is a porting/refactoring work in progress: do not use any of the source code until a official release has been drafted.

## Installation

- Clone this repository
- Go to the directory where you cloned it
- Run `pip install .`

## CLI

The package also has a command line interface bound to `radardef`:

```
usage: radardef [-h] [-p] [-v] {convert,format,download} ...

Radar data tool box

positional arguments:
  {convert,format,download}
                        Avalible command line interfaces
    convert             Convert the target files to a supported format
    format              Returns the source format of the file
    download            Download data files from the given radar (Only Eiscat is supported for now)

optional arguments:
  -h, --help            show this help message and exit
  -p, --profiler        Run profiler
  -v, --verbose         Increase output verbosity
```

## Contributing

Please refer to the style and contribution guidelines documented in the
[IRF Software Contribution Guide](https://danielk.developer.irf.se/software_contribution_guide/).
Generally external code-contributions are made trough a "Fork-and-pull"
workflow, while internal contributions follow the branching strategy outlined
in the contribution guide.
