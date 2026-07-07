"""
rename_coordinates.py

Renames ERA5 coordinate names from "latitude"/"longitude" to
"lat"/"lon" so they are compatible with workflows that expect the
same coordinate convention as UTCI datasets.

The input NetCDF file is overwritten in place.
"""

import os
import xarray as xr


def rename_lat_lon(netcdf_path):
    """
    Renames the coordinate and dimension names of a NetCDF file from
    ``latitude``/``longitude`` to ``lat``/``lon``.

    This is useful for making ERA5 datasets compatible with workflows
    that expect the coordinate naming convention used by UTCI datasets.

    Parameters
    ----------
    netcdf_path : str
        Path to the NetCDF file to update.

    Returns
    -------
    None
        The input file is overwritten with the renamed coordinates.
    """
    dataset = xr.open_dataset(netcdf_path)

    rename_dict = {}

    if "latitude" in dataset.coords or "latitude" in dataset.dims:
        rename_dict["latitude"] = "lat"

    if "longitude" in dataset.coords or "longitude" in dataset.dims:
        rename_dict["longitude"] = "lon"

    if not rename_dict:
        print("coordinates already renamed.")
        dataset.close()
        return

    dataset = dataset.rename(rename_dict)

    dataset.load()
    dataset.close()

    os.remove(netcdf_path)
    dataset.to_netcdf(netcdf_path)

    print(f"Updated NetCDF file: {netcdf_path}")