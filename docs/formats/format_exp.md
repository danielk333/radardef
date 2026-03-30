# Experiment definition

The experiment section is defined by [ExpDef](../reference/radardef/types/types.md#radardef.types.types.experiment.ExpDef), it is a dataclass containing the specifications for defining the rx and tx signal. The parameters are:

- **name**: Name of experiment.
- **radar_frequency**: Radar frequency
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
- **tx_channel** (_optional_): As not all radars are transmitting this is optional.
- **t_cal_on_usec** (_optional_): Calibration on time in microseconds.
- **t_cal_off_usec** (_optional_): Calibration off time in microseconds.
- **code**: Tx signal code.
