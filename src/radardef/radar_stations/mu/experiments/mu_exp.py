import numpy as np

from radardef.types import ExpDef

mu_exp = ExpDef(
    name="mu_experiment",
    radar_frequency=46.5,
    t_ipp_usec=3120,
    t_samp_usec=6,
    t_rx_start_usec=486,
    t_rx_end_usec=486 + 6 * 85,
    t_tx_start_usec=0,
    t_tx_end_usec=26 * 6,  # (code length * (baud_length/t_samp)) * t_samp
    baud_length_usec=12,
    code=np.array(
        [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
        dtype=np.float64,
    ),
    rx_channels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
    samples_per_file=512 * 520 * 12,
)

mu_exp_large = ExpDef(
    name="mu_experiment",
    radar_frequency=46.5,
    t_ipp_usec=3120,
    t_samp_usec=6,
    t_rx_start_usec=486,
    t_rx_end_usec=486 + 6 * 85,
    t_tx_start_usec=0,
    t_tx_end_usec=26 * 6,  # (code length * (baud_length/t_samp)) * t_samp
    baud_length_usec=12,
    code=np.array(
        [1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1],
        dtype=np.float64,
    ),
    rx_channels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
    samples_per_file=512 * 520 * 14,
)
