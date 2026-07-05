"""
mask_convert.py
Masks a NetCDF file to a geographic region (using a shapefile) and converts
its data from Kelvin to Celsius, saving the result to a new .nc file.
Originally built for UTCI (ERA5-HEAT), but the masking is generic: it works
for any region, as long as you give it the right .shp (Mexico, another
country, a state, whatever).
"""
from __future__ import annotations
import argparse
import geopandas as gpd
import rioxarray
import xarray as xr


def load_region_geometry(shapefile_path, dissolve=True, crs="EPSG:4326"):
    region = gpd.read_file(shapefile_path)
    region = region.to_crs(crs)
    if dissolve:
        region = region.dissolve()
    return region


def prepare_dataset(ds, x_dim="lon", y_dim="lat", crs="EPSG:4326"):
    ds = ds.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    ds = ds.rio.write_crs(crs)
    return ds


def clip_to_region(ds, region_gdf, drop=False):
    return ds.rio.clip(region_gdf.geometry, region_gdf.crs, drop=drop)


def kelvin_to_celsius(dataset_or_variable):
    return dataset_or_variable - 273.15


def mask_netcdf(
    netcdf_path,
    shapefile_path,
    output_path,
    variable="utci",
    x_dim="lon",
    y_dim="lat",
    crs="EPSG:4326",
    drop=False,
):
    with xr.open_dataset(netcdf_path) as ds:
        ds = prepare_dataset(ds, x_dim=x_dim, y_dim=y_dim, crs=crs)
        region = load_region_geometry(shapefile_path, crs=crs)
        ds_region = clip_to_region(ds, region, drop=drop)
        ds_region = ds_region.load()

    ds_region[variable] = kelvin_to_celsius(ds_region[variable])

    return ds_region
