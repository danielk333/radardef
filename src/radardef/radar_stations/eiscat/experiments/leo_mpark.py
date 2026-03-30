from radardef.radar_stations.eiscat.experiments import load_radar_code
from radardef.types import ExpDef

leo_mpark_2_1u = ExpDef(
    name="leo_mpark_2.1u",
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
