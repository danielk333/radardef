# # Antenna gain
# ---
# Radardef contains models for the gain patterns of all pre-defined radar systems
import matplotlib.pyplot as plt
import numpy as np

import radardef.radar_stations as radar_stations
from radardef.types import BeamType, EiscatUHFLocation

# ## Get the radars
# ---
loc = EiscatUHFLocation.TROMSO
radar_mes = radar_stations.EiscatUHF(location=loc, beam_type=BeamType.MEASURED)
radar_cas = radar_stations.EiscatUHF(location=loc, beam_type=BeamType.CASSEGRAIN)
radar_mu = radar_stations.Mu()

# ## Gain compare
# ---


def get_hpbw(ze, gains):
    """Half-power beam-width (note the power, not pure gain)"""
    root = np.argmax(np.max(gains) * 0.5 - gains > 0)
    return ze[root] * 2, 10 * np.log10(gains[root])


num = 1000
az = np.zeros((num,))
ze = np.linspace(0, 6, num)

params = radar_mes.beam_parameters.copy()
params.pointing = np.array([0, 0, 1])
gains_mes = radar_mes.beam.sph_gain(az, 90 - ze, params, degrees=True)

params_cas = radar_cas.beam_parameters.copy()
params_cas.pointing = np.array([0, 0, 1])
gains_cas = radar_cas.beam.sph_gain(az, 90 - ze, params_cas, degrees=True)

gains_mu = radar_mu.beam.sph_gain(az, 90 - ze, radar_mu.beam_parameters, degrees=True)

fig, ax = plt.subplots()
ax.plot(ze, np.log10(gains_mes) * 10, label="EiscatUHF Measured")
ax.plot(ze, np.log10(gains_cas) * 10, label="EiscatUHF Cassegrain")
ax.plot(ze, np.log10(gains_mu) * 10, label="MU Array")
#
theta_hpbw, g_hpbw_db = get_hpbw(ze, gains_cas)
ax.plot(theta_hpbw / 2, g_hpbw_db, "xr", label=f"EiscatUHF Cassegrain HPBW = {theta_hpbw:.1f} deg")
#
theta_hpbw, g_hpbw_db = get_hpbw(ze, gains_mu)
ax.plot(theta_hpbw / 2, g_hpbw_db, "or", label=f"MU Array HPBW = {theta_hpbw:.1f} deg")
#
ax.set_ylim(0, None)
ax.set_xlabel("Off-axis angle [deg]")
ax.set_ylabel("Gain [dB]")
ax.legend()
#
plt.show()
