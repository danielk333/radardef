from radardef.radar_stations.eiscat.experiments import load_radar_code
from radardef.types import ExpDef

leo_pwait_2_3r = ExpDef(
    name="leo_pwait_2.3r",
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
    rx_channels=["sod"],
    tx_channel="sod",
)

leo_pwait_2_3u = ExpDef(
    name="leo_pwait_2.3u",
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
)


leo_pwait_2_3v = ExpDef(
    name="leo_pwait_2.3v",
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
)


leo_pwait_2_4u = ExpDef(
    name="leo_pwait_2.4u",
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
)

leo_pwait_2_5u = ExpDef(
    name="leo_pwait_2.5u",
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
)
