
# CLI
---
The cli supports data processing for the already available radars.

The available commands can be seen with:

```bash
    $ radardef -h
```
or, *where subcommand is format/convert/download*

```bash
    $ radardef <subcommand> -h
```

## Format
---
The **format** tool is used to get the source type of a file or directory or just see the available supported
formats.

Available formats:

```bash
    $ radardef format -l

    >mui
    >eiscat_matbz
```

Get format of file

```bash
    $ radardef format path/to/random/file/MUI123467

    Source format is: mui
```
## Convert
---
The **convert** tool is used to convert one or several files to **one** format.

Available converters

```bash
    $ radardef convert -l .

    mui:
    ├Target format> h5
    eiscat_matbz:
    ├Target format> drf
```

Convert one file, output in /tmp:

```bash

    $ radardef convert path/to/random/file/MUI123467 h5 tmp/
```
Convert multiple files:

```bash
    $ tree /data -L 2
    /data/
    ├── mu1
    │   ├── MUI123454
    │   └── MUI123455
    ├── mu2
    │   ├── MUI123456
    │   ├── MUI123457
    │   └── MUI123458
    └── mu3
        └── MUI123459

    $ radardef convert /data h5 tmp/
```

## Download
---
Use the **download** tool to download radar data.

!!! Warning
    Currently, **download**
    functionality is not working, once it does it will only support eiscat data.

```bash
    $ radardef download -h
    $ radardef download eiscat -h
    $ radardef -v download eiscat 20220408 leo_bpark_2.1u_NO uhf /data --progress
```