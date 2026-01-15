# # Load data
# ---
# After the data has been converted to a compatible format we can load it in a standardized way.
# When a file/directory is loaded a data loader object is returned which allows one to access meta data,
# bounds and access to read data from the measurement.

# Workaround to make jupyter notebook find utils
import sys
import os
from pathlib import Path

sys.path.insert(1, str(Path(os.path.abspath("")) / "docs" / "examples"))

import radardef
from radardef.types import EiscatUHFLocation, TargetFormat
from pathlib import Path
import tempfile
import radardef
import numpy as np
import matplotlib.pyplot as plt
import utils
import numpy.typing as npt

# ## Prerequisites - download and convert data
# ---

raw_data_dir = tempfile.TemporaryDirectory()
converted_data_path = tempfile.TemporaryDirectory()
raw_data = utils.download_test_data(Path(raw_data_dir.name))
radar_def = radardef.RadarDef()
converted_files = radar_def.convert(raw_data, TargetFormat.H5, converted_data_path.name)

# ## Option 1 - RadarDef object
# ---
# Here we use the RadarDef object to load the data, the file type and compatible dataloader is
# automatically recognized.

data_loader = radar_def.load_data(converted_files[0][0])
assert data_loader is not None, "No data loader compatible with the file"

# ## Option 2 - Specific radar station
# ---
# When working with data from a specific station the station object can be used instead.

data_loader = radardef.Mu().load_data(converted_files[0][0])
assert data_loader is not None, "MU h5 data loader is not compatible with the filetype"

# ## Option 3 - using a collection of several stations dataloaders
# ---
# If data from some specific stations should be analysed a collection can be used.

dl_collection = radardef.DataLoaderCollection([radardef.Mu(), radardef.EiscatUHF(EiscatUHFLocation.KIRUNA)])
data_loader = dl_collection.load_data(converted_files[0][0])
assert data_loader is not None, "No data loader compatible with the file"

# ## Available data
# ---
# Here some datapoints are available and a example on how to read samples from the data.

print(f"Metadata exp: {data_loader.meta.experiment}")
print(f"Metadata bounds: {data_loader.meta.bounds}")
print(f"Available channels: {data_loader.channels}")
channel = data_loader.channels[0]
channel_bounds = data_loader.bounds(channel)
print(f"Channel sample bounds: {channel_bounds}")
print(
    f"First 10 samples: {data_loader.read(channel=channel, start_sample=channel_bounds[0], vector_length=10)}"
)
print(f"Pointing data: {data_loader.pointing}")

# ## Plotting the raw data
# ---
# The RX samples can be visualised as below. To get a better resolution we sum all
# channels. The data source is the MU radar, thus we use the Mu station object:

data_loader = radardef.Mu().load_data(converted_files[0][0])
print(f"Available channels: {data_loader.channels}")
summed_data = np.zeros((data_loader.bounds(channel=data_loader.channels[0])[1],), dtype=np.complex128)
for chnl in data_loader.channels:
    summed_data += data_loader.read(chnl)

# Extract receiver samples from each pulse,


def rx_samples_per_pulse(data: npt.NDArray, meta: radardef.types.Metadata):
    """Extract rx samples from each pulse"""
    pulses = int(len(summed_data) / meta.experiment.ipp_samps)
    samples_per_pulse = summed_data.reshape(pulses, meta.experiment.ipp_samps)
    rx_start_samp = meta.experiment.t_rx_start_usec / meta.experiment.t_samp_usec
    rx_end_samp = meta.experiment.t_rx_end_usec / meta.experiment.t_samp_usec
    rx_samples_per_pulse = samples_per_pulse[:, int(rx_start_samp) - 1 : int(rx_end_samp) - 1]
    return rx_samples_per_pulse


# $(\mathbf{A^T})^2$

rti_data = np.abs(rx_samples_per_pulse(summed_data, data_loader.meta).T) ** 2

# Plot measurement

fig, ax = plt.subplots(figsize=(8, 6))
ax.pcolormesh(rti_data)
ax.set_xlabel("Inter Pulse Periods")
ax.set_ylabel("Range-samples")
ax.set_title(f"{raw_data.name} Range-Time-Intensity")

# There is a sign of a object at the start of the measurement, to verify this this we can choose to only read
# a certain amount of samples, lets say the first 500 ipps.

summed_data = np.zeros((500 * data_loader.meta.experiment.ipp_samps,), dtype=np.complex128)
for chnl in data_loader.channels:
    summed_data += data_loader.read(chnl, vector_length=500 * data_loader.meta.experiment.ipp_samps)

# $(\mathbf{A^T})^2$

rti_data = np.abs(rx_samples_per_pulse(summed_data, data_loader.meta).T) ** 2

# Plot measurement, here we can see a clear indication of a object.

fig1, ax1 = plt.subplots(figsize=(8, 6))
ax1.pcolormesh(rti_data)
ax1.set_xlabel("Inter Pulse Periods")
ax1.set_ylabel("Range-samples")
ax1.set_title(f"{raw_data.name} Range-Time-Intensity")
plt.show()
# Clear files
raw_data_dir.cleanup()
converted_data_path.cleanup()
