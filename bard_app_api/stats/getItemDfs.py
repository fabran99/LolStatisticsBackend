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
    str).str.contains("Trinket")))]['id'].astype(int).tolist()
# Items finales
final_form_items = list(df_items.loc[~(df_items['tags'].astype(
    str).str.contains("Trinket|Consumable")) &
    ~(df_items['name'].astype(str).str.contains("Encantamiento"))]['id'].astype(int).unique())
# Botas
boots = list(df_items.loc[(df_items['tags'].astype(
    str).str.contains("Boots"))]['id'].astype(int).unique())
# GoldPer
support_items = list(df_items.loc[(
    (df_items['tags'].astype(str).str.contains("GoldPer")))]['id'].astype(int).unique())
# Jungle items
jungle_items = list(df_items.loc[(df_items['tags'].astype(
    str).str.contains("Jungle"))]['id'].astype(int).unique())
