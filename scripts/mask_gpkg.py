"""
build_mask.py
Generates a single-file mask (GeoPackage, .gpkg) from a shapefile made up of
multiple region parts (e.g. INEGI's 00ent.shp, with one polygon per state),
dissolving them into a single national polygon. Meant to be run once; the
resulting .gpkg is then reused by mask_convert.py without needing to
re-dissolve or keep the original shapefile's multiple files around.
"""
import argparse

from mask_convert import load_region_geometry


def build_country_mask(shapefile_path, output_path, dissolve=True, crs="EPSG:4326"):
    """
    Loads a shapefile (possibly made of several parts, e.g. one polygon per
    state) and saves it as a single GeoPackage file, already dissolved into
    one polygon if dissolve=True.

    shapefile_path: path to the source .shp (e.g. INEGI's 00ent.shp).
    output_path: where to save the resulting .gpkg.
    dissolve: whether to merge all parts into a single polygon before saving.
              Set to False if the source is already a single polygon and you
              just want to convert file formats.
    crs: coordinate reference system to reproject to before saving.
    """
    region = load_region_geometry(shapefile_path, dissolve=dissolve, crs=crs)
    region.to_file(output_path, driver="GPKG")
    return region


def _main():
    parser = argparse.ArgumentParser(
        description="Builds a single-file (.gpkg) mask from a multi-part shapefile."
    )
    parser.add_argument("shapefile_path", help="Path to the source .shp (e.g. INEGI's 00ent.shp).")
    parser.add_argument("output_path", help="Path to save the resulting .gpkg.")
    parser.add_argument("--crs", default="EPSG:4326", help="CRS to reproject to (default: EPSG:4326).")
    parser.add_argument(
        "--no-dissolve", action="store_true",
        help="Skip dissolving into a single polygon (use if the source is already a single polygon).",
    )
    args = parser.parse_args()

    region = build_country_mask(
        shapefile_path=args.shapefile_path,
        output_path=args.output_path,
        dissolve=not args.no_dissolve,
        crs=args.crs,
    )

    print(f"Saved -> {args.output_path}")
    print(f"Polygons in file: {len(region)}")


if __name__ == "__main__":
    _main()