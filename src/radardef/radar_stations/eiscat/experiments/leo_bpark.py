from radardef.radar_stations.eiscat.experiments import load_radar_code
from radardef.types import ExpDef

leo_bpark_2_0 = ExpDef(
    name="leo_bpark_2.0",
    radar_frequency=930,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["uhf"],
    tx_channel="uhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)
leo_bpark_2_0u = ExpDef(
    name="leo_bpark_2.0u",
    radar_frequency=930,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["uhf"],
    tx_channel="uhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)


leo_bpark_2_1u = ExpDef(
    name="leo_bpark_2.1u",
    radar_frequency=930,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["uhf"],
    tx_channel="uhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)

# note : ambiguous wrt channel - could be 32m or 42m
leo_bpark_2_2 = ExpDef(
    name="leo_bpark_2.2",
    radar_frequency=500.5,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["32m"],
    tx_channel="32m",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)


leo_bpark_2_3v = ExpDef(
    name="leo_bpark_2.3v",
    radar_frequency=224,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["vhf"],
    tx_channel="vhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)

leo_bpark_2_4u = ExpDef(
    name="leo_bpark_2.4u",
    radar_frequency=930,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["uhf"],
    tx_channel="uhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)


leo_bpark_2_5u = ExpDef(
    name="leo_bpark_2.5u",
    radar_frequency=930,
    t_ipp_usec=20000,
    t_samp_usec=1,
    t_tx_start_usec=82,
    t_tx_end_usec=2002,
    t_rx_start_usec=0,
    t_rx_end_usec=20000,
    baud_length_usec=30,
    code=load_radar_code("leo_bpark"),
    t_cal_on_usec=19900,
    t_cal_off_usec=19997,
    samples_per_file=12800000,
    rx_channels=["uhf"],
    tx_channel="uhf",
    fir_filter="b414d15_gaus",  # TODO: Apply correct filter
)
