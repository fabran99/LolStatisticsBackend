from .ddragon_routes import get_champ_loading_img,get_champ_square_img, get_champ_passive_img,get_champ_skill_img, get_champ_splashart_img
from .ddragon_routes import get_all_champ_data,get_champ_data
from .ddragon_routes import get_item_img,get_all_item_data
from .ddragon_routes import get_all_summoners_data,get_summoner_img
from .ddragon_routes import get_all_icon_data, get_icon_img
from .ddragon_routes import get_current_version, get_all_maps

from .mongodb import get_mongo_assets,get_saved_version

from datetime import datetime as dt
import re

db = get_mongo_assets()

def load_data(force=False):
    """
    Carga los datos de la version actual a mongo
    """
    saved_version = get_saved_version()
    game_version = get_current_version()

    if saved_version == game_version and not force:
        return None
    
    # Actualizo la version por la actual
    current_data = db.metadata.find_one({})
    new_data = {"current_version":game_version, "updated":dt.utcnow()}
    if current_data:
        db.metadata.replace_one({"_id":current_data['_id']}, new_data)
    else:
        db.metadata.insert_one(new_data)

    # Cargo datos de campeones
    load_champ_data()

    # Datos de objetos
    load_item_data()

    # Datos de summs
    load_summ_data()

    # Datos de iconos
    load_icon_data()

    
def load_champ_data():
    """
    Cargo la info de los campeones a mongo
    """

    print("========================")
    print("Inicio proceso de campeones")
    print("========================")

    champ_data = get_all_champ_data()
    champ_data = champ_data['data']

    fixed_data = []

    for key,value in champ_data.items():
        new_value = {}
        print("Trayendo datos de {}".format(value['name']))
        # Datos
        new_value['id'] = value['id']
        new_value['key'] = value['key']
        new_value['name'] = value['name']
        new_value['title'] = value['title']
        new_value['tags'] = value['tags']

        # Imagenes
        new_value['images']={
            "splashart":get_champ_splashart_img(value['id']),
            "loading":get_champ_loading_img(value['id']),
            "square":get_champ_square_img(value['id'])
        }
       

        # Detalles
        detailed_data = get_champ_data(value['id'])['data'][value['id']]
        
        # Tips
        new_value['allytips']=detailed_data['allytips']
        new_value['enemytips']=detailed_data['enemytips']

        # Skins
        new_value['skins']=[]
        for x in detailed_data['skins']:
            if x['num'] != 0:
                skin_data = x
                skin_data['images']={
                    "splashart":get_champ_splashart_img(value['id'], x["num"]),
                    "loading":get_champ_loading_img(value['id'],x['num'])
                }
                new_value['skins'].append(skin_data)

        # Skills
        new_value['skills']=[]
        for x in detailed_data['spells']:
            skill_data = {
                "id":x['id'],
                "name":x['name'],
                "description":sanitize_skill_desc(x['description']),
                "image":get_champ_skill_img(x['image']['full'])
            }
            new_value['skills'].append(skill_data)
        
        # Pasiva
        new_value['passive']={
            "name":detailed_data['passive']['name'],
            "description":sanitize_skill_desc(detailed_data['passive']['description']),
            "image":get_champ_passive_img(detailed_data['passive']['image']['full'])
        }

        # Agrego a la lista
        fixed_data.append(new_value)

    # Guardo en mongo
    for champ in fixed_data:
        print("Actualizando datos de {}".format(champ['name']))
        db.champ.replace_one({"id":champ['id']}, champ, upsert=True)


def load_item_data():
    """
    Carga a mongo los datos de los items
    """
    print("========================")
    print("Inicio proceso de objetos")
    print("========================")
    item_data = get_all_item_data()
    item_data = item_data['data']

    fixed_data = []

    maps = get_all_maps()
    maps = {str(x['mapId']):x['mapName'] for x in maps}

    for key, value in item_data.items():
        print("Trayendo datos de {}".format(value['name']))
        data = {
           "id":key,
           "name":value['name'],
           "description":value['plaintext'],
           "price":value['gold']['total'],
           "image":get_item_img(value['image']['full']),
           "maps":[maps[x] for x,y in value['maps'].items() if y]
        }
        fixed_data.append(data)

    # Inserto en mongo
    for item in fixed_data:
        print("Actualizando datos de {}".format(item['name']))
        db.item.replace_one({"id":item['id']}, item, upsert=True)
        

def load_summ_data():
    """
    Guarda los datos de los summoners en mongo
    """
    print("========================")
    print("Inicio proceso de summoners")
    print("========================")
    summ_data = get_all_summoners_data()
    summ_data = summ_data['data']

    fixed_data = []
    for key,value in summ_data.items():
        data = {
            "id":value['id'],
            "name":value['name'],
            "description":value['description'],
            "cooldown":value['cooldownBurn'],
            "key":value['key'],
            "image":get_summoner_img(value['image']['full'])
        }
        fixed_data.append(data)

    # Inserto en mongo
    for summ in fixed_data:
        print("Actualizando datos de {}".format(summ['name']))
        db.summ.replace_one({"id":summ['id']}, summ, upsert=True)
    

def load_icon_data():
    """
    Carga datos de los iconos
    """ 
    print("========================")
    print("Inicio proceso de iconos")
    print("========================")
    icon_data = get_all_icon_data()
    icon_data = icon_data['data']

    fixed_data = []

    for key, value in icon_data.items():
        data ={
            "id":value['id'],
            "image":get_icon_img(value['image']['full'])
        }
        fixed_data.append(data)
    
    # Inserto en mongo
    for icon in fixed_data:
        print("Actualizando datos de ícono {}".format(icon['id']))
        db.icon.replace_one({"id":icon['id']}, icon, upsert=True)

    
def sanitize_skill_desc(description):
    """
    Quita elementos html de las descripciones de skill
    """
    return re.sub('<[^<]+?>', '', description)