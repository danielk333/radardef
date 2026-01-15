# # Sky temperature
# ---
# By using the specifications of the radar station one can using the sky temperature tools visualise the
# sky temperatures

from astropy.time import Time
from pygdsm import GlobalSkyModel16, GSMObserver16
import matplotlib.pyplot as plt
import radardef.tools.sky_temperature as sky_temperature
import radardef.radar_stations as radar_stations
import spacecoords.projection as proj
import pyant

# ## Sky temperature map
# ---

radar = radar_stations.Mu()
gsm = GlobalSkyModel16(freq_unit="Hz")
mm = gsm.generate(radar.frequency)

gsm.view(logged=False)

time = Time("2025-11-10T00:00:00", format="isot", scale="utc")
az, el, tmp = sky_temperature.temperature_map(radar, time, 300)

fig, ax = plt.subplots(figsize=(8, 8))
hx, hy = proj.latlon_to_hammer(az, el)
ax.pcolor(hx, hy, tmp[:-1, :-1])

# ## Gain heatmap
# ---

ov = GSMObserver16()
ov.lon = radar.lon
ov.lat = radar.lat
ov.elev = radar.alt
ov.date = time.datetime

ov.generate(radar.frequency * 1e-6)  # type: ignore
ov.view(logged=False)
ov.view_observed_gsm(logged=False)

pyant.plotting.gain_heatmap(
    radar.beam,
    radar.beam_parameters,
    min_elevation=80,
    cbar_min=0,
)

# ## Calculate sky temperature
# ---

sky_ant_temperature = sky_temperature.calculate_antenna_temperature(radar, time, 300)
print(f"{sky_ant_temperature=} K")

plt.show()
