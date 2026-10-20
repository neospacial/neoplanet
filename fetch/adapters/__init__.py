"""Adapter registry. The key is the 'adapter' field in sources.json."""
from . import climate, erddap, firms, gdacs, jpl, nasa, ndbc, silso, storms, swpc, tsunami, usgs

ADAPTERS = {
    "swpc_scales": swpc.swpc_scales,
    "swpc_alerts": swpc.swpc_alerts,
    "swpc_table": swpc.swpc_table,
    "swpc_records": swpc.swpc_records,
    "swpc_goes": swpc.swpc_goes,
    "swpc_flares": swpc.swpc_flares,
    "swpc_rtsw": swpc.swpc_rtsw,
    "swpc_ovation": swpc.swpc_ovation,
    "swpc_hemi_power": swpc.swpc_hemi_power,
    "swpc_text": swpc.swpc_text,
    "swpc_45day": swpc.swpc_45day,
    "nasa_donki": nasa.nasa_donki,
    "jpl_cad": jpl.jpl_cad,
    "jpl_fireball": jpl.jpl_fireball,
    "jpl_sentry": jpl.jpl_sentry,
    "silso_csv": silso.silso_csv,
    "usgs_quakes": usgs.usgs_quakes,
    "usgs_volcano": usgs.usgs_volcano,
    "tsunami_atom": tsunami.tsunami_atom,
    "gdacs": gdacs.gdacs,
    "nasa_eonet": nasa.nasa_eonet,
    "nhc_storms": storms.nhc_storms,
    "ibtracs": storms.ibtracs,
    "firms": firms.firms,
    "erddap_grid": erddap.erddap_grid,
    "ncei_cag": climate.ncei_cag,
    "gistemp": climate.gistemp,
    "gml_csv": climate.gml_csv,
    "nsidc": climate.nsidc,
    "cpc_oni": climate.cpc_oni,
    "cpc_nino_weekly": climate.cpc_nino_weekly,
    "cpc_daily": climate.cpc_daily,
    "ozone_watch": climate.ozone_watch,
    "bom_mjo": climate.bom_mjo,
}

# Adapters that fetch more than one URL. They have the form fetch(ds, ctx) -> result.
FETCHERS = {
    "usgs_geomag": usgs.usgs_geomag,
    "ndbc_dart": ndbc.ndbc_dart,
    "star_gmsl": climate.star_gmsl,
}


def get(name):
    return FETCHERS.get(name), ADAPTERS.get(name)
