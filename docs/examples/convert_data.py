# # Convert data
# ---
# Radardef supports conversion of the raw data to one or several formats. This is done to only extract the
# the needed data and to simplify reading the data later.

# Workaround to make jupyter notebook find utils
import sys
import os
from pathlib import Path

sys.path.insert(1, str(Path(os.path.abspath("")) / "docs" / "examples"))

import tempfile
import radardef
from radardef.types import EiscatUHFLocation, TargetFormat
import utils

# ## Prerequisites - download and convert data
# ---

raw_data_dir = tempfile.TemporaryDirectory()
converted_data_path = tempfile.TemporaryDirectory()
raw_data = utils.download_test_data(Path(raw_data_dir.name))

# ## Option 1 - using the RadarDef object
# ---
# In this case we are using the RadarDef object to convert the data. The RadarDef object is a collection
# of all radarstations and all their tools in one place. The advantage of this object is that a compatible
# converter is found by the object itself, thus it can be possible to convert several different formats to
# one unified format.

radar_def = radardef.RadarDef()
converted_files = radar_def.convert(raw_data, TargetFormat.H5, converted_data_path.name)
utils.print_dir_items(converted_files[0])  # TODO: Fix this 0

# ## Option 2 - using a specific radar station
# ---
# If the data is strictly coming from one radarstation then there is no need to use the RadarDef object.
# The radar station itself can then be used instead as below.

station = radardef.Mu()
converted_files = station.convert(raw_data, TargetFormat.H5, Path(converted_data_path.name))
utils.print_dir_items(converted_files)


# ## Option 3 - using a collection of several station converters
# ---
# In this case we have a collection of two stations, in the case of a collection it is neccessary to
# manually check what data type the raw data is.

stations = [radardef.Mu(), radardef.EiscatUHF(EiscatUHFLocation.KIRUNA)]
source_format = radardef.FormatCollection(stations).get_format(raw_data)
print(f"The source format is: {source_format}")

# After this we can convert the data using the collection

conv_collection = radardef.ConverterCollection(stations)
converted_files = conv_collection.convert(raw_data, source_format, TargetFormat.H5, converted_data_path.name)
utils.print_dir_items(converted_files)

# Clear files
raw_data_dir.cleanup()
converted_data_path.cleanup()
