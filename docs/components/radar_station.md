# Radar station
---
A radar station is the full description of a radar station. It shall (*if available*) contain radar station
specifications, the stations source format [validator](radar_station.md#validator) , data format [converter](radar_station.md#converter) and [data loader](radar_station.md#data-loader) to be able to extract data to one or several
usable format.

With all this it is possible to quickly access radar station specifications and process
measurement data.

See [examples/radar_station](../examples/radar_station.py) for more details.

## Specifications
---
Each radar must contain the following specifications:

- [station_id](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.station_id)
- [transmitter](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.transmitter)
- [receiver](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.receiver)
- [lat](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.lat)
- [lon](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.lon)
- [alt](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.alt)
- [beam](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.beam)
- [beam_parameters](../reference/radardef/components/radar_station_template.md#radardef.components.radar_station_template.RadarStation.beam_parameters)

From this we can determine the precise location of the station and with the [beam](https://danielk.developer.irf.se/pyant/reference/pyant/beam/)
the radiation pattern can be defined. For more beam examples see [pyant](https://danielk.developer.irf.se/pyant/examples/)


## Data processing components
---
To handle the "raw" data from a radarstation the following components are needed.

### Validator
The [Validator](../reference/radardef/components/validator_template.md) is a very simple class, it is used to map a [SourceFormat/TargetFormat/String](../reference/radardef/types/formats.md#radardef.types.formats.SourceFormat) to a specific
data format to be able to map file formats to radars, converters or loaders.


### Converter

The [Converter](../reference/radardef/components/converter_template.md) object is used to describe exactly what it sounds like, a converter.
Something that transforms data from one format to another.

Each converter object must include the property [source_format](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.source_format)
and [target_format](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.target_format). This shall describe the format it
converts from and what format it converts too. Furthermore a
[converter](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.convert) needs to be declared.

The source format is any string but for the known objects we use the string enum [SourceFormat](../reference/radardef/types/formats.md#radardef.types.formats.SourceFormat),
and likewise for the target format [TargetFormat](../reference/radardef/types/formats.md#radardef.types.formats.TargetFormat).

The convert function must accept a list of paths as input and output a list of paths containing
the path to the converted files.

See [examples/convert_data](../examples/convert_data.py) for more details.

#### Input restrictions

Stucture to be able to handle multiple directories

<span style="color: green;">Ok</span>

```bash
    /data/
    ├── leo_bpark_2.1u_NO@uhf
    │   ├── 20220408_08
    │   └── 20220408_09
    └── mu
        ├── MUI123456
        └── MUI123457
```

<span style="color: green;">Ok</span>

```bash
    /data/
    ├── leo_bpark_2.1u_NO@uhf
    │   ├── 20220408_08
    │   └── 20220408_09
    └── mu
        ├── mu1
        │   ├── MUI123456
        │   └── MUI123457
        └── mu2
            └── MUI123458

```
<span style="color: red;">Not ok</span>

```bash
    /data/
    └── mu
        ├── MUI123456
        ├── MUI123457
        └── leo_bpark_2.1u_NO@uhf
            ├── 20220408_08
            └── 20220408_09
```

In the case above the mu folder will be recognized as a mui only folder and the converter will fail when
trying to convert the leo_bpark_2.1u_NO@uhf.

<span style="color: red;">Not ok</span>

```bash
    /data/
    ├── leo_bpark_2.1u_NO@uhf
    │   ├── 20220408_08
    │   └── 20220408_09
    └── mu
        ├── MUI123459
        ├── mu1
        │   ├── MUI123456
        │   └── MUI123457
        └── mu2
            └── MUI123458
```

Here *MUI123459* will be ignored/lost as the converter will only convert the root directories.


### Data loader

A dataloader should read and load data from a file to a standardized usable format.

A dataloader is at most times connected to converted files e.g from *MUI* to *H5*, therefore the dataloader
contains the parameter [converted_format](../reference/radardef/components/data_loader_template.md#radardef.components.data_loader_template.DataLoader.converted_format)
to map what files are compatible with the loader.

Each data loader is mapped to a [Validator](../reference/radardef/components/validator_template.md),
this is to validate the compability of any file with the loader, if not compatible no point in loading the file.
The entry point of the class is the [load](../reference/radardef/components/data_loader_template.md#radardef.components.data_loader_template.DataLoader.load) function, if load is not called the [DataLoader](../reference/radardef/components/data_loader_template.md) is useless.
What load does is extracting and chaching the metadata and path, in this way there is no need to store the whole
file in RAM.

The [Metadata](../reference/radardef/types/types.md#radardef.types.types.Metadata) is a named tuple containing the measurements static variables, it has been split into two data types,
[BoundParams](../reference/radardef/types/types.md#radardef.types.types.BoundParams) and [ExpParams](../reference/radardef/types/types.md#radardef.types.types.ExpParams). More details about the Metadata is available at [Format-MetaData](../formats/format_meta.md)

To get actual measurement points from the data loader one can request the needed samples from the
[Read](../reference/radardef/components/data_loader_template.md#radardef.components.data_loader_template.DataLoader.read)
function.

See [examples/load_data](../examples/load_data.py) for more details.



