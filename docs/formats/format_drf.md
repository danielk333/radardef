
# DRF Format
---


This describes **DRF**, one of the available target formats.

The **Hargtarget_DRF** format is an instance of the **Digital_RF** format for
reading and writing radio frequency data. **Digital_RF** is defined by the
Python module [digital-rf](https://pypi.org/project/digital-rf/), and is based on the **HDF5** format, a
self-documenting format intended for efficient data storage and random access
for data processing. The fileformat includes two data channels. One channel
contains the radar signal, in this case this is the channel named *uhf*. The
seconds channel contains data describing the pointing direction of the radar
antenna, for the same time period. Typically, the two channels are sampled
at very different sample rates.

As **Digital_RF** does not allow arbitrary meta
information, **Hardtarget_DRF** additionally specifies an extra metadata file
**metadata.ini** at the top level of the folder tree.


```bash

    drf
    ├── metadata.ini
    ├── uhf
    │   ├── 2021-04-12T11-00-00
    │   │   ├── rf@1618228761.000.h5
    │   │   ├── rf@1618228762.000.h5
    │   │   ├── rf@1618228763.000.h5
    │   │   ├── rf@1618228764.000.h5
    │   │   ├── ...
    │   └── drf_properties.h5
    └── pointing
        ├── 2021-04-12T11-00-00
        │   ├── rf@1618228761.000.h5
        └── drf_properties.h5
```





