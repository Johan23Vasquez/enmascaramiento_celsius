"""
mask_convert.py

Masks a NetCDF file to a geographic region (using a shapefile).

Optionally converts a selected variable from Kelvin to Celsius.
Originally built for UTCI (ERA5-HEAT), but the masking is generic:
it works for any region as long as you provide the appropriate
shapefile (country, state, municipality, etc.).
"""

import argparse
import geopandas as gpd
import rioxarray
import xarray as xr


def load_region_geometry(shapefile_path, dissolve=True, crs="EPSG:4326"):
    """
    Loads a region shapefile and returns its geometry.

    Parameters
    ----------
    shapefile_path : str
        Path to the shapefile or vector file defining the region.
    dissolve : bool, default=True
        If True, merges all geometries into a single polygon.
    crs : str, default="EPSG:4326"
        Coordinate reference system to reproject the geometry to.

    Returns
    -------
    geopandas.GeoDataFrame
        Region geometry in the requested CRS.
    """
    region = gpd.read_file(shapefile_path)
    region = region.to_crs(crs)

    if dissolve:
        region = region.dissolve()

    return region


def prepare_dataset(dataset, x_dim="lon", y_dim="lat", crs="EPSG:4326"):
    """
    Prepares a dataset for spatial operations with rioxarray.

    Parameters
    ----------
    dataset : xarray.Dataset
        Input dataset.
    x_dim : str, default="lon"
        Name of the longitude dimension.
    y_dim : str, default="lat"
        Name of the latitude dimension.
    crs : str, default="EPSG:4326"
        Coordinate reference system of the dataset.

    Returns
    -------
    xarray.Dataset
        Dataset configured for spatial clipping.
    """
    dataset = dataset.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    dataset = dataset.rio.write_crs(crs)

    return dataset


def clip_to_region(dataset, region_gdf, drop=False):
    """
    Clips a dataset to the supplied region.

    Parameters
    ----------
    dataset : xarray.Dataset
        Dataset prepared with ``prepare_dataset``.
    region_gdf : geopandas.GeoDataFrame
        Region geometry.
    drop : bool, default=False
        If False, preserves the original grid and fills cells outside
        the region with NaN. If True, crops the dataset to the region's
        bounding box.

    Returns
    -------
    xarray.Dataset
        Clipped dataset.
    """
    return dataset.rio.clip(region_gdf.geometry, region_gdf.crs, drop=drop)


def kelvin_to_celsius(data):
    """
    Converts temperatures from Kelvin to Celsius.

    Parameters
    ----------
    data : xarray.Dataset or xarray.DataArray
        Input data.

    Returns
    -------
    xarray.Dataset or xarray.DataArray
        Data converted to degrees Celsius.
    """
    return data - 273.15


def mask_netcdf(
    netcdf_path,
    shapefile_path,
    variable="utci",
    convert_to_celsius=True,
    x_dim="lon",
    y_dim="lat",
    crs="EPSG:4326",
    drop=False,
):
    """
    Clips a NetCDF dataset to a geographic region.

    Optionally converts the selected variable from Kelvin to Celsius.

    Parameters
    ----------
    netcdf_path : str
        Path to the input NetCDF file.
    shapefile_path : str
        Path to the region shapefile.
    variable : str, default="utci"
        Variable to convert if ``convert_to_celsius`` is True.
    convert_to_celsius : bool, default=True
        Whether to convert the selected variable from Kelvin to Celsius.
    x_dim : str, default="lon"
        Name of the longitude dimension.
    y_dim : str, default="lat"
        Name of the latitude dimension.
    crs : str, default="EPSG:4326"
        Coordinate reference system.
    drop : bool, default=False
        Whether to crop the dataset to the region's bounding box.

    Returns
    -------
    xarray.Dataset
        Dataset clipped to the selected region. If
        ``convert_to_celsius`` is True, the selected variable is
        returned in degrees Celsius.
    """
    with xr.open_dataset(netcdf_path) as dataset:
        dataset = prepare_dataset(dataset, x_dim=x_dim, y_dim=y_dim, crs=crs)
        region = load_region_geometry(shapefile_path, crs=crs)
        dataset = clip_to_region(dataset, region, drop=drop)
        dataset = dataset.load()

    if convert_to_celsius:
        dataset[variable] = kelvin_to_celsius(dataset[variable])

    return dataset