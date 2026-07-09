"""
convert_units.py

Utilidades para convertir variables acumuladas de ERA5 (J/m^2) a
potencia promedio (W/m^2).
"""


def convert_ssrd_to_wm2(dataset, variable="ssrd", accumulation_seconds=3600):
    """
    Converts a radiation variable from accumulated J/m² to average W/m².

    In ERA5, radiation variables like SSRD are accumulated over the period
    between time steps. For hourly data, this period is 3600 seconds, so
    dividing by that value gives the average power (W/m²) during that hour.

    Parameters
    ----------
    dataset : xarray.Dataset
        Input dataset containing the variable to convert.
    variable : str, default="ssrd"
        Name of the variable to convert.
    accumulation_seconds : int, default=3600
        Length of the accumulation period in seconds. Use 3600 for
        hourly ERA5 data. Change this if your data has a different
        time step (e.g., 10800 for 3-hourly data).

    Returns
    -------
    xarray.Dataset
        Dataset with the variable converted to W/m², with updated
        units attribute if present.
    """
    dataset = dataset.copy()
    dataset[variable] = dataset[variable] / accumulation_seconds

    if "units" in dataset[variable].attrs:
        dataset[variable].attrs["units"] = "W m**-2"

    return dataset