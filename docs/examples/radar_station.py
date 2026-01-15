# # Radar station
# ---
#
# Radar stations can be used and accessed in several different ways
#
# ## Option 1 - Radar def
# ---
# A radar station can be accessed from the radar definition object, which is a collection of all
# radar stations, the available radars can be seen as:

import random
from radardef import RadarDef, radar_stations, RadarStation
from radardef.types import EiscatUHFLocation, BeamType

radar_def = RadarDef()
available_stations = radar_def.radar_stations
print(f"Available radar stations: {available_stations}")

# A simple function to show some station details in a short clear format


def station_details(station: RadarStation) -> None:
    print(f"Station: {station.station_id}")
    print(f"    Location, alt: {station.alt}, lon: {station.lon}, lat: {station.lat}")
    print(f"    Transmitter: {station.transmitter}, Receiver: {station.receiver}")
    print(f"    Frequency: {station.frequency}")


# The wanted station (random in this case) can then be extracted as simple as below, note
# that it is needed to check that we recived a station.

ind = random.randint(a=0, b=len(available_stations) - 1)
station = radar_def.get_radar(available_stations[ind])
if station is not None:
    station_details(station)
else:
    raise Exception("Station not found!")


# ## Option 2 - Access station right away
# ---
# Many times only a specific station is needed and it can the easily be accessed like this, in this example we
# use the eiscat uhf station. The finess of using the station right away is that we can more easily configure
# it, here with both location and beam type.

stations = [
    radar_stations.EiscatUHF(EiscatUHFLocation.KIRUNA, BeamType.MEASURED),
    radar_stations.EiscatUHF(EiscatUHFLocation.SODANKYLA, BeamType.CASSEGRAIN),
]
for station in stations:
    station_details(station)

# ## Creating a custom radar station
# ---
# When the existing stations are not enough it is possible to create your own stations.
# A simple example is as below, a station with a isotropic beam, it can both recive and transmit and
# it has the same data components as some eiscat stations, Ta-da a new radar stations is in place.

from pyant.models import Isotropic, IsotropicParams
from radardef.radar_stations.eiscat.converters import EiscatMatbzToDrf
from radardef.radar_stations.eiscat.data_loaders import DrfLoader
from radardef.radar_stations.eiscat.validators import EiscatMatlab

orodruin = RadarStation(
    station_id="Orodruin",
    transmitter=True,
    receiver=True,
    lat=-39.156833,
    lon=175.632167,
    alt=1371,
    beam=Isotropic(),
    beam_parameters=IsotropicParams(),
    converters=[EiscatMatbzToDrf()],
    validator=EiscatMatlab(),
    data_loaders=[DrfLoader()],
)

# The station can then be added with the rest of the collection if wanted

radar_def.add_radar(orodruin)
print(radar_def.radar_stations)
