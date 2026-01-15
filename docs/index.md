# Radardef
---
The radardef library contains radar station definitions, a station definition
contains information about location, power, beam, data types, data processing
tools such as converters and loaders etc.
The aim of the library is to create a common definition of a radar station to make
one unified way of station specifications and data handling.
By doing so data can from several different stations can be handled by the same tool,
this tool is [RadarDef](reference/radardef/radar_def.md).

With [RadarDef](reference/radardef/radar_def.md) it is possible to convert and load
data from several stations at once with no need to specify their origins.
But often the source of the data is from one specific station and in those cases the
already existing stations are available aswell:

   - [MU](reference/radardef/radar_stations/mu/mu.md)
   - [Pansy](reference/radardef/radar_stations/pansy/pansy.md)
   - Eiscat radars:
      - [Eiscat 3D](reference/radardef/radar_stations/eiscat/eiscat_3d.md)
      - [Eiscat Svalbard Radar (ESR)](reference/radardef/radar_stations/eiscat/esr.md)
      - [Tromso Space Debris Radar (TSDR)](reference/radardef/radar_stations/eiscat/tsdr.md)
      - [Eiscat UHF](reference/radardef/radar_stations/eiscat/eiscat_uhf.md)
      - [Eiscat VHF](reference/radardef/radar_stations/eiscat/eiscat_vhf.md)

## New stations
---
To create a new station just follow the [RadarStation](reference/radardef/components/radar_station_template.md)
template, an example is available at [Examples/Radar Station](examples/radar_station.py).
Once created it can be added to the collections or be used on its own just as any other.

## Getting started
---
To install

```bash
   pip install radardef
```
or the nightly build

```bash
   git clone --branch develop git@github.com:danielk333/radardef.git
   cd radardef
   pip install .
```

