# Metadata
---
Metadata is just a gathering of [Experiment](format_meta.md#experiment) and [Bounds](format_meta.md#bounds)


## Experiment
The experiment section is defined by [ExpParams](../reference/radardef/types/types.md#radardef.types.types.ExpParams), it is a NamedTuple containing parameters defining the rx and tx signal. The parameters are:

- **name**: Name of measurement.
- **radar_frequency**:  Radar frequency
- **t_ipp_usec**: Length of inter pulse period, in microseconds
- **ipp_samps**: Amount of samples per inter pulse period
- **sample_rate**: Amount of samples sent during one second.
- **t_samp_usec**: Length of one sample, or time between two samples, in microseconds.
- **rx_channels**: List of all Rx channels.
- **t_rx_start_usec**: Rx signal start in the inter pulse period, in microseconds.
- **t_rx_end_usec**: Rx signal end in the inter pulse period, in microseconds.
- **t_tx_start_usec**: Tx signal start in the inter pulse period, in microseconds.
- **t_tx_end_usec**: Tx signal end in the inter pulse period, in microseconds.
- **wavelength**: The signal wavelength.
- **tx_channel** (*optional*): As not all radars are transmitting this is optional.
- **tx_pulse_length** (*optional*): Amount of samples in tx signal.
- **t_cal_on_usec** (*optional*): Calibration on time in microseconds.
- **t_cal_off_usec** (*optional*): Calibration off time in microseconds.
- **data** (*optional*): To be removed
- **code**: Tx signal code.
- **pulse** (*optional*): To be removed

## Bounds
---
Bounds defines when the measurement was taken, it is defined by [BoundParams](../reference/radardef/types/types.md#radardef.types.types.BoundParams)

- **ts_start_usec**: Start of mesurement, in microseconds since epoch.
- **ts_end_usec**: End of mesurement, in microseconds since epoch.
