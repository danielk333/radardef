# Radar station

---

A radar station is the full description of a radar station. It shall (_if available_) contain radar station
specifications, the stations source format [validator](radar_station.md#validator) , data format [converter](radar_station.md#converter) and [data loader](radar_station.md#data-loader) to be able to extract data to one or several
usable format.

With all this it is possible to quickly access radar station specifications and process
measurement data.

See [examples/radar_station](../examples/radar_station.py) for more details.

## Specifications

---

Each radar must contain the following specifications:

- [station_id](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.station_id)
- [transmitter](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.transmitter)
- [receiver](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.receiver)
- [lat](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.lat)
- [lon](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.lon)
- [alt](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.alt)
- [beam](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.beam)
- [beam_parameters](../reference/radardef/radar_station.md#radardef.radar_station.RadarStation.beam_parameters)

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
Something that transforms data from one format to another.o.

Each converter is declared with a[source_format](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.source_format)
and [target_format](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.target_format). This shall describe the format it
converts from and what format it converts too.

To convert a compatible file the [convert](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.convert) can be called, it handles both single files and directories of files.
To define how to convert a single object of the given source format each convert class will have its unique
[\convert_single_object](../reference/radardef/components/converter_template.md#radardef.components.converter_template.Converter.convert_single_object) function. This will define the converters functionality, only needed to support one file/object as the Converter class handles the rest.

The source format is any string but for the known objects we use the string enum [SourceFormat](../reference/radardef/types/formats.md#radardef.types.formats.SourceFormat),
and likewise for the target format [TargetFormat](../reference/radardef/types/formats.md#radardef.types.formats.TargetFormat).

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

### Data loader

A dataloader should read and load data from a file to a standardized usable format.

A dataloader is at most times connected to converted files e.g from _MUI_ to _H5_, therefore the dataloader
contains the parameter [converted_format](../reference/radardef/components/data_loader_template.md#radardef.components.data_loader_template.DataLoader.converted_format)
to map what files are compatible with the loader.

Each data loader is mapped to a [Validator](../reference/radardef/components/validator_template.md),
this is to validate the compability of any file with the loader, if not compatible no point in loading the file.

The data loader accepts a custom [ExpDef](../reference/radardef/types/types.md#radardef.types.types.ExpDef) which is the experiment definition. This isto properly be able to decode the data. If none is provided the loader will try to find a suitable experiment definition dependent on the file name.

To get actual measurement points from the data loader one can request the needed samples from the
[Read](../reference/radardef/components/data_loader_template.md#radardef.components.data_loader_template.DataLoader.read)
function.

See [examples/load_data](../examples/load_data.py) for more details.
