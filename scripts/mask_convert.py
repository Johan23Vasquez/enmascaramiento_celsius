"""
mask_convert.py
Masks a NetCDF file to a geographic region (using a shapefile) and converts
its data from Kelvin to Celsius, saving the result to a new .nc file.
Originally built for UTCI (ERA5-HEAT), but the masking is generic: it works
for any region, as long as you give it the right .shp (Mexico, another
country, a state, whatever).
"""
import argparse
import geopandas as gpd
import rioxarray
import xarray as xr


def load_region_geometry(shapefile_path, dissolve=True, crs="EPSG:4326"):
    """
    Loads a shapefile for a region (country, state, whatever) and returns
    it as a single polygon (if dissolve=True) in the requested CRS.

    shapefile_path: path to the .shp of the region you want to use as a mask.
    """
    region = gpd.read_file(shapefile_path)
    region = region.to_crs(crs)
    if dissolve:
        region = region.dissolve()
    return region


def prepare_dataset(netCDF, x_dim="lon", y_dim="lat", crs="EPSG:4326"):
    """
    Gets the dataset ready to be clipped: tells rioxarray which are the
    spatial dimensions and which CRS to use.
    """
    netCDF = netCDF.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    netCDF = netCDF.rio.write_crs(crs)
    return netCDF


def clip_to_region(netCDF, region_gdf, drop=False):
    """
    Clips a dataset (already prepared with prepare_dataset) to the polygon
    in region_gdf. drop=False keeps the original grid and sets NaN outside
    the region; drop=True also shrinks the array to the region's bounding box.
    """
    return netCDF.rio.clip(region_gdf.geometry, region_gdf.crs, drop=drop)


def kelvin_to_celsius(dataset_or_variable):
    """
    Converts from Kelvin to Celsius by subtracting 273.15.
    Works the same whether you pass a full Dataset or just a DataArray/variable.
    """
    return dataset_or_variable - 273.15


def mask_netcdf(
    netcdf_path,
    shapefile_path,
    variable="utci",
    x_dim="lon",
    y_dim="lat",
    crs="EPSG:4326",
    drop=False,
):
    """
    Clips a NetCDF to a region (using its shapefile), converts that
    variable from Kelvin to Celsius, and returns the result.

    The returned Dataset contains the full original grid with NaN outside
    the region (or a cropped grid if drop=True), already in Celsius. Note
    that this version does not save to disk -- ds_region.to_netcdf(output_path)
    is commented out below; uncomment it if you want the result written to
    output_path.
    """
    with xr.open_dataset(netcdf_path) as netCDF:
        netCDF = prepare_dataset(netCDF, x_dim=x_dim, y_dim=y_dim, crs=crs)
        region = load_region_geometry(shapefile_path, crs=crs)
        netCDF_region = clip_to_region(netCDF, region, drop=drop)
        netCDF_region = netCDF_region.load()

    netCDF_region[variable] = kelvin_to_celsius(netCDF_region[variable])

    # ds_region.to_netcdf(output_path)
    return netCDF_region
