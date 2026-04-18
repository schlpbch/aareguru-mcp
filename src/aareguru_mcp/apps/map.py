"""App 8: Interactive Leaflet.js map of Aare monitoring locations."""

import json
from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    Column,
    Embed,
    Grid,
    Muted,
    Text,
)

from ._constants import (
    _AG_BFU,
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_TEMP,
    _DK,
    _FONT_CSS,
    _SAFETY_LEVELS,
)

logger = structlog.get_logger(__name__)

map_app = FastMCPApp("map")

# Safety-level colors for Leaflet markers (index = level-1, matches _SAFETY_LEVELS order)
# Using the WCAG-AA hex values from _SAFETY_LEVELS; last entry covers "Sehr hoch"
_MARKER_COLORS = [color for _, _, _, color in _SAFETY_LEVELS] + ["#7f1d1d"]


def _safety_color(flow: float | None) -> str:
    """Return hex color for a flow value, matching _SAFETY_LEVELS thresholds."""
    if flow is None:
        return "#9ca3af"
    thresholds = [t for t, _, _, _ in _SAFETY_LEVELS]
    colors = [c for _, _, _, c in _SAFETY_LEVELS] + ["#7f1d1d"]
    for i, t in enumerate(thresholds):
        if flow < t:
            return colors[i]
    return colors[-1]


def _build_map_html(cities_geo: list[dict[str, Any]], focus_city: str | None) -> str:
    """Return a self-contained Leaflet.js HTML string for embedding as srcdoc."""

    cities_json = json.dumps(cities_geo, ensure_ascii=False)

    # Determine initial view: fly to focus_city if given, else fit all markers
    if focus_city:
        focus_json = json.dumps(focus_city)
    else:
        focus_json = "null"

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aare Karte</title>
<style>
  html,body,#map {{
    margin:0;padding:0;width:100%;height:100%;
    background:#f0f4f8;
    font-family:'DIN Next LT Pro',ui-sans-serif,system-ui,sans-serif;
  }}
  @media(prefers-color-scheme:dark){{
    html,body{{background:#1c3138;}}
  }}
  .leaflet-popup-content-wrapper{{
    border-radius:3px !important;
    box-shadow:0 2px 8px rgba(15,64,95,.18) !important;
  }}
  .leaflet-popup-content{{
    margin:10px 14px !important;
    font-family:inherit;
    font-size:13px;
    line-height:1.5;
  }}
  .ag-popup-city{{
    font-weight:900;
    font-size:14px;
    color:#0f405f;
    text-transform:uppercase;
    letter-spacing:.05em;
    margin-bottom:4px;
  }}
  .ag-popup-temp{{
    font-size:22px;
    font-weight:900;
    color:#0877ab;
    line-height:1;
  }}
  .ag-popup-meta{{
    color:#0f405f;
    opacity:.7;
    font-size:11px;
    margin-top:2px;
  }}
  .ag-popup-desc{{
    font-style:italic;
    color:#0f405f;
    opacity:.65;
    font-size:11px;
  }}
  .ag-popup-safety{{
    display:inline-block;
    padding:1px 6px;
    border-radius:3px;
    font-size:10px;
    font-weight:700;
    letter-spacing:.07em;
    text-transform:uppercase;
    margin-top:4px;
    color:#fff;
  }}
  #sat-toggle{{
    position:absolute;
    top:10px;right:10px;
    z-index:1000;
    background:rgba(255,255,255,0.92);
    border:none;
    border-radius:3px;
    padding:5px 10px;
    font-size:11px;
    font-weight:700;
    letter-spacing:.08em;
    text-transform:uppercase;
    color:#0f405f;
    cursor:pointer;
    box-shadow:0 1px 4px rgba(15,64,95,.2);
    transition:background .15s;
  }}
  #sat-toggle:hover{{background:rgba(255,255,255,1);}}
  #sat-toggle.active{{background:#0f405f;color:#2be6ff;}}
  @media(prefers-color-scheme:dark){{
    #sat-toggle{{background:rgba(28,49,56,0.92);color:#88bee0;}}
    #sat-toggle:hover{{background:rgba(28,49,56,1);}}
    #sat-toggle.active{{background:#88bee0;color:#1c3138;}}
  }}
</style>
</head>
<body>
<div id="map"></div>
<button id="sat-toggle">Satellit</button>
<script>
(function(){{
  var CITIES = {cities_json};
  var FOCUS  = {focus_json};
  var LS_KEY = 'aareguru-map-state';
  var LS_SAT = 'aareguru-map-satellite';

  function loadLeaflet(cb){{
    if(window.L){{cb();return;}}
    var link=document.createElement('link');
    link.rel='stylesheet';
    link.href='https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);
    var s=document.createElement('script');
    s.src='https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    s.onload=cb;
    document.head.appendChild(s);
  }}

  function initMap(){{
    var L=window.L;
    var darkMode=window.matchMedia('(prefers-color-scheme:dark)').matches;

    // Restore last view + satellite preference from localStorage
    var saved=null;
    try{{saved=JSON.parse(localStorage.getItem(LS_KEY));}}catch(e){{}}
    var satellite=false;
    try{{satellite=JSON.parse(localStorage.getItem(LS_SAT))||false;}}catch(e){{}}

    var defaultCenter=[46.95,7.45];
    var defaultZoom=8;
    var initCenter=saved?[saved.lat,saved.lng]:defaultCenter;
    var initZoom=saved?saved.zoom:defaultZoom;

    var map=L.map('map',{{
      center:initCenter,
      zoom:initZoom,
      zoomControl:true,
      attributionControl:true
    }});

    // Tile layer definitions
    var baseUrl=darkMode
      ?'https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png'
      :'https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png';

    var baseLayer=L.tileLayer(baseUrl,{{
      attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      subdomains:'abcd',
      maxZoom:19
    }});

    // ESRI World Imagery — free, no API key
    var satLayer=L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}',
      {{
        attribution:'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        maxZoom:19
      }}
    );

    // Start with persisted preference
    (satellite?satLayer:baseLayer).addTo(map);

    // Toggle button
    var btn=document.getElementById('sat-toggle');
    if(satellite)btn.classList.add('active');

    btn.addEventListener('click',function(){{
      satellite=!satellite;
      if(satellite){{
        map.removeLayer(baseLayer);
        satLayer.addTo(map);
        btn.classList.add('active');
      }}else{{
        map.removeLayer(satLayer);
        baseLayer.addTo(map);
        btn.classList.remove('active');
      }}
      try{{localStorage.setItem(LS_SAT,JSON.stringify(satellite));}}catch(e){{}}
    }});

    // Persist map position
    function saveState(){{
      var c=map.getCenter();
      try{{localStorage.setItem(LS_KEY,JSON.stringify({{lat:c.lat,lng:c.lng,zoom:map.getZoom()}}));}}catch(e){{}}
    }}
    map.on('moveend zoomend',saveState);

    // Add markers
    var markers={{}};
    var bounds=[];

    CITIES.forEach(function(c){{
      if(!c.lat||!c.lon)return;
      bounds.push([c.lat,c.lon]);

      var r=Math.max(7,Math.min(14,8+(c.temp||0)/3));
      var marker=L.circleMarker([c.lat,c.lon],{{
        radius:r,
        color:'#fff',
        weight:2,
        fillColor:c.color,
        fillOpacity:0.9
      }});

      var safetyStyle='background:'+c.color;
      var popup=[
        '<div class="ag-popup-city">'+c.name+'</div>',
        c.temp!==null
          ?'<div class="ag-popup-temp">'+c.temp.toFixed(1)+'°C</div>'
          :'<div class="ag-popup-temp">—</div>',
        '<div class="ag-popup-meta">Abfluss: '+(c.flow!==null?Math.round(c.flow)+' m³/s':'—')+'</div>',
        c.desc?'<div class="ag-popup-desc">'+c.desc+'</div>':'',
        '<span class="ag-popup-safety" style="'+safetyStyle+'">'+c.safety+'</span>'
      ].join('');

      marker.bindPopup(popup,{{maxWidth:200}});
      markers[c.city]=marker;
      marker.addTo(map);
    }});

    // Fly to focus city, or fit all markers if no focus
    if(FOCUS&&markers[FOCUS]){{
      map.setView(markers[FOCUS].getLatLng(),13);
      markers[FOCUS].openPopup();
    }}else if(!saved&&bounds.length>0){{
      map.fitBounds(bounds,{{padding:[24,24]}});
    }}
  }}

  loadLeaflet(initMap);
}})();
</script>
</body>
</html>"""


@map_app.tool()
async def refresh_map(city: str | None = None) -> dict[str, Any]:
    """Refresh map data (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    cities = await service.get_cities_list()
    compare = await service.compare_cities(None)
    return {"cities": cities, "compare": compare, "focus": city}


@map_app.ui()
async def aare_map(city: str | None = None) -> PrefabApp:
    """Show an interactive OpenStreetMap with all Aare monitoring stations.

    Each city is plotted as a circle marker coloured by BAFU safety level.
    Click a marker to see temperature, flow, and Swiss German description.

    Args:
        city: Optional city identifier to fly to on load (e.g. 'Bern', 'Thun').
              Omit to show all cities with the map fitted to bounds.
    """
    logger.info("app.aare_map", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()

    # Fetch coordinates + live conditions in parallel
    cities_list, compare_data = await _fetch_map_data(service)

    # Build a lookup from city id → compare data
    compare_by_city: dict[str, dict[str, Any]] = {
        c.get("city", ""): c for c in (compare_data.get("cities") or [])
    }

    # Merge into geo-enriched list for Leaflet
    cities_geo: list[dict[str, Any]] = []
    for item in cities_list:
        city_id = item.get("city", "")
        coords = item.get("coordinates") or {}
        lat = coords.get("lat")
        lon = coords.get("lon")
        if lat is None or lon is None:
            continue

        live = compare_by_city.get(city_id, {})
        flow = live.get("flow")
        temp = live.get("temperature") if live else item.get("aare")
        desc = live.get("temperature_text") or ""
        safety_label = _safety_label(flow)
        color = _safety_color(flow)

        cities_geo.append(
            {
                "city": city_id,
                "name": item.get("longname") or item.get("name") or city_id,
                "lat": lat,
                "lon": lon,
                "temp": temp,
                "flow": flow,
                "desc": desc,
                "safety": safety_label,
                "color": color,
            }
        )

    warmest = compare_data.get("warmest") or {}
    safe_count: int = compare_data.get("safe_count", 0)
    total: int = compare_data.get("total_count", len(cities_geo))

    map_html = _build_map_html(cities_geo, city)

    with Column(gap=0, cssClass="p-2 max-w-4xl mx-auto") as view:
        Text(
            "Aare Karte",
            cssClass=f"text-base font-black tracking-tight text-[{_AG_TXT_PRIMARY}]"
            f" dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )

        # Summary strip — same pattern as city_finder / compare
        with Grid(columns=3, gap=0, cssClass="mb-1"):
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        warmest.get("location") or warmest.get("city") or "—",
                        cssClass=f"text-sm font-black text-[{_AG_WASSER_TEMP}]"
                        f" dark:text-[{_DK.WASSER_TEMP}]",
                    )
                    if warmest.get("temperature") is not None:
                        Text(
                            f"{warmest['temperature']:.1f}°",
                            cssClass=f"text-xl font-black tabular-nums"
                            f" text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                        )
                    Muted(
                        "WÄRMSTE STADT",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}]"
                f" dark:border-t-[{_DK.BFU}]"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        f"{safe_count} / {total}",
                        cssClass=f"text-xl font-black tabular-nums"
                        f" text-[{_AG_BFU}] dark:text-[{_DK.BFU}]",
                    )
                    Muted(
                        "SICHERE STÄDTE",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_TXT_PRIMARY}]/30"
                f" dark:border-t-[{_DK.TXT_PRIMARY}]/30"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        str(len(cities_geo)),
                        cssClass=f"text-xl font-black tabular-nums"
                        f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                    )
                    Muted(
                        "STATIONEN",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

        # Map embed
        with Card(cssClass=f"{_AG_RADIUS} overflow-hidden"):
            Embed(html=map_html, height="440px", cssClass="w-full block")

    return PrefabApp(
        view=view,
        state={"city": city, "total": len(cities_geo), "safe_count": safe_count},
        stylesheets=[_FONT_CSS],
    )


async def _fetch_map_data(
    service: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch cities list and compare data concurrently."""
    import asyncio

    cities_task = asyncio.create_task(service.get_cities_list())
    compare_task = asyncio.create_task(service.compare_cities(None))
    cities_list, compare_data = await asyncio.gather(cities_task, compare_task)
    return cities_list, compare_data


def _safety_label(flow: float | None) -> str:
    """Return German safety label for a flow value."""
    if flow is None:
        return "Unbekannt"
    thresholds_labels = [(t, lbl) for t, lbl, _, _ in _SAFETY_LEVELS]
    for threshold, label in thresholds_labels:
        if flow < threshold:
            return label
    return "Sehr hoch"
