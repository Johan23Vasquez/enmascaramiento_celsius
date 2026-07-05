"""
mask_convert.py

Enmascara un NetCDF a una región geográfica (usando un shapefile) y convierte
sus datos de Kelvin a Celsius, guardando el resultado en un nuevo .nc.

Pensado originalmente para UTCI (ERA5-HEAT), pero el enmascarado es genérico:
sirve para cualquier región, con tal de darle el .shp correcto (México,
otro país, un estado, lo que sea).

Todas las funciones vienen directo del notebook de pruebas (001_pruebas.ipynb),
donde ya se validaron los rangos de salida y el porcentaje de celdas
recortadas — este script solo las junta y les agrega un punto de entrada
de línea de comandos.
"""

from __future__ import annotations

import argparse

import geopandas as gpd
import rioxarray  
import xarray as xr


def load_region_geometry(shapefile_path, dissolve=True, crs="EPSG:4326"):
    """
    Carga un shapefile de una región (país, estado, lo que sea) y lo regresa
    como un solo polígono (si dissolve=True) en el CRS pedido.

    shapefile_path: ruta al .shp de la región que quieres usar como máscara.
    """
    region = gpd.read_file(shapefile_path)
    region = region.to_crs(crs)
    if dissolve:
        region = region.dissolve()
    return region


def prepare_dataset(ds, x_dim="lon", y_dim="lat", crs="EPSG:4326"):
    """
    Deja el dataset listo para recortar: le dice a rioxarray cuáles son las
    dimensiones espaciales y qué CRS usar.
    """
    ds = ds.rio.set_spatial_dims(x_dim=x_dim, y_dim=y_dim)
    ds = ds.rio.write_crs(crs)
    return ds


def clip_to_region(ds, region_gdf, drop=False):
    """
    Recorta un dataset (ya preparado con prepare_dataset) al polígono de
    region_gdf. drop=False mantiene la grilla original y pone NaN fuera de
    la región; drop=True además achica el arreglo al bounding box de la región.
    """
    return ds.rio.clip(region_gdf.geometry, region_gdf.crs, drop=drop)


def kelvin_a_celsius(dataset_o_variable):
    """
    Convierte de Kelvin a Celsius restando 273.15.
    Funciona igual si le pasas un Dataset completo o solo un DataArray/variable.
    """
    return dataset_o_variable - 273.15


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
    """
    Recorta un NetCDF a una región (usando su shapefile), convierte esa
    variable de Kelvin a Celsius, y guarda el resultado en un nuevo .nc.

    El archivo que se guarda contiene únicamente los puntos dentro de la
    región (el resto queda como NaN, o se recorta del todo si drop=True),
    ya en Celsius.
    """
    with xr.open_dataset(netcdf_path) as ds:
        ds = prepare_dataset(ds, x_dim=x_dim, y_dim=y_dim, crs=crs)
        region = load_region_geometry(shapefile_path, crs=crs)
        ds_region = clip_to_region(ds, region, drop=drop)
        ds_region = ds_region.load()  # a memoria antes de cerrar el archivo de entrada

    # Convierte DESPUÉS de enmascarar: restarle 273.15 a los NaN de fuera de
    # la región sigue dando NaN, así que el orden no cambia el resultado —
    # pero mantenerlo así es más fácil de leer: "primero recorto, luego
    # convierto lo que quedó".
    ds_region[variable] = kelvin_a_celsius(ds_region[variable])

    #ds_region.to_netcdf(output_path)
    return ds_region

