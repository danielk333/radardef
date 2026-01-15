import astropy.units as u
import numpy as np
import numpy.typing as npt
from astropy.coordinates import AltAz, EarthLocation, Galactic
from astropy.time import Time
from astropy_healpix import HEALPix
from pygdsm import GlobalSkyModel16

from radardef.components.radar_station_template import RadarStation


def temperature_map(
    radar: RadarStation, time: Time, res: int, flatten: bool = False
) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
    """Temperature map"""
    az_mat, el_mat = np.meshgrid(
        np.linspace(0, 2 * np.pi, num=res),
        np.linspace(0, np.pi / 2, num=res),
    )
    shape = az_mat.shape
    az_mat = az_mat.reshape((az_mat.size,))
    el_mat = el_mat.reshape((el_mat.size,))

    gsm = GlobalSkyModel16(freq_unit="Hz", include_cmb=True)
    mm = gsm.generate(radar.frequency)
    hp_obj = HEALPix(nside=gsm.nside, order="RING", frame=Galactic)
    coords = AltAz(
        az=az_mat * u.rad,
        alt=el_mat * u.rad,
        obstime=time,
        location=EarthLocation(
            lat=radar.lat * u.deg,
            lon=radar.lon * u.deg,
        ),
    )
    temp_mat = hp_obj.interpolate_bilinear_skycoord(coords, mm)
    if not flatten:
        az_mat = az_mat.reshape(shape)
        el_mat = el_mat.reshape(shape)
        temp_mat = temp_mat.reshape(shape)
    return az_mat, el_mat, temp_mat


def calculate_antenna_temperature(radar: RadarStation, time: Time, res: int) -> float:
    """Calculate antena temperature"""
    az_mat, el_mat, temp_mat = temperature_map(radar, time, res, flatten=True)
    g_mat = radar.beam.sph_gain(
        azimuth=az_mat,
        elevation=el_mat,
        parameters=radar.beam_parameters,
    )
    g_mat = g_mat.flatten()  # type: ignore
    d_az = 2 * np.pi / res
    d_el = np.pi / 2 / res
    d_S = np.cos(el_mat) * d_az * d_el

    # ugly numerical integration
    g_int = np.sum(g_mat * d_S)
    t_int = np.sum(temp_mat * g_mat * d_S)

    return t_int / g_int
