from lol_stats_api.helpers.mongodb import get_monary, get_mongo_assets

db = get_mongo_assets()

def get_all_champs_name_id():
    """
    Devuelve una lista de todos los campeones,con su name
    y su id de mongo
    """

    all_data = db.champ.find({},{"_id":1,"name":1,"key":1})
    data_dict = {}
    for x in all_data:
        data_dict[x['key']]={
                "name":x['name']
            }

    return data_dict


def get_all_items_data(final_form_only=False):
    """
    Devuelve la lista de items como un dict donde sus id
    son la key
    """

    all_items = db.item.find({})
    if final_form_only:
        data_dict ={}

        for x in all_items:
            if x['final_form']:
                if "Consumable" in x['tags'] and not "Vision" in x['tags']:
                    continue
                if "Lane" in x['tags'] and (not "GoldPer" in x['tags'] and not "Vision" in x['tags']):
                    continue

                data_dict[x['id']]=x
        
    else:
        data_dict = {
            x['id']:x for x in all_items
        }
        
    return data_dict
