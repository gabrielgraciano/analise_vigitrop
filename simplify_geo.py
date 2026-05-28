# simplify_geo.py — rode UMA VEZ no terminal
import geopandas as gpd

print("Lendo arquivo original...")
gdf = gpd.read_file("brasil_municipios.json")

print(f"Features: {len(gdf)} | Colunas: {list(gdf.columns)}")

print("Simplificando geometrias...")
gdf["geometry"] = gdf.geometry.simplify(tolerance=0.05, preserve_topology=True)

print("Salvando...")
gdf.to_file("brasil_municipios_simpl.geojson", driver="GeoJSON")

print("Pronto! 'brasil_municipios_simpl.geojson' gerado.")