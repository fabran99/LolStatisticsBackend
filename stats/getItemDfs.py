from assets.get_assets_mongodb import get_all_items_data
import pandas as pd

# =================================
# Item clases
# =================================
df_all_items = pd.DataFrame(get_all_items_data(final_form_only=False)).T[[
    "name", "id", "price", 'final_form', "tags"]]
# Busco items que esten en su forma final
df_items = pd.DataFrame(get_all_items_data(final_form_only=True)).T[[
    "name", "id", "price", 'final_form', "tags"]]
# Items de vision
trinkets = df_items.loc[((df_items['tags'].astype(
    str).str.contains("Trinket")))]['id'].tolist()
# Items finales
final_form_items = df_items.loc[~(df_items['tags'].astype(
    str).str.contains("Trinket|Consumable")) &
    ~(df_items['name'].astype(str).str.contains("Encantamiento"))]['id'].unique()
# Botas
boots = df_items.loc[(df_items['tags'].astype(
    str).str.contains("Boots"))]['id'].tolist()
# GoldPer
support_items = df_items.loc[(
    (df_items['tags'].astype(str).str.contains("GoldPer")))]['id'].unique()
# Jungle items
jungle_items = df_items.loc[(df_items['tags'].astype(
    str).str.contains("Jungle"))]['id'].unique()
