import requests
from django.conf import settings

DEF_LANG=settings.DEF_LANGUAGE

# ===============================
# Requests de ddragon para assets
# ===============================

# Maps
def get_all_maps():
    
    r = requests.get("https://static.developer.riotgames.com/docs/lol/maps.json")
    return r.json()

# Champs
def get_current_version():
    """
    Devuelve la version actual de league of legends
    """
    r = requests.get("https://ddragon.leagueoflegends.com/api/versions.json")
    versions=r.json()
    last_version = versions[0]

    return last_version


def get_all_champ_data(lang=DEF_LANG):
    """
    Devuelve el listado completo de champs con sus datos
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/champion.json".format(str(saved_version),str(lang))
    print(saved_version)
    r = requests.get(url)
    data = r.json()
    return data


def get_champ_data(champ, lang=DEF_LANG):
    """
    Devuelve la informacion de un champ seleccionado
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/champion/{}.json".format(str(saved_version),str(lang),str(champ))

    r = requests.get(url)
    data = r.json()
    return data


def get_champ_splashart_img(champ, skin=0):
    """
    Devuelve la url de el splashart de un champ
    """
    url = "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{}_{}.jpg".format(str(champ), str(skin))
    return url


def get_champ_loading_img(champ, skin=0):
    """
    Devuelve la url de la imagen de carga de un champ
    """
    url = "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{}_{}.jpg".format(str(champ), str(skin))
    return url


def get_champ_square_img(champ):
    """
    Devuelve la url de la imagen square de un champ
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/champion/{}.png".format(str(saved_version), str(champ))
    return url


def get_champ_passive_img(name):
    """
    Devuelve la url de la imagen de la pasiva de un champ
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/passive/{}".format(str(saved_version), str(name))
    return url


def get_champ_skill_img(name):
    """
    Devuelve la url de la imagen de una skill
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/spell/{}".format(str(saved_version),str(name))
    return url


# Items
def get_all_item_data(lang=DEF_LANG):
    """
    Devuelve la info de todos los items
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/item.json".format(str(saved_version), str(lang))
    r = requests.get(url)
    return r.json()


def get_item_img(item):
    """
    Devuelve la imagen de un item por su id
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/item/{}".format(str(saved_version), str(item))
    return url


# Summs
def get_all_summoners_data(lang=DEF_LANG):
    """
    Devuelve la info de todos los summoners
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/summoner.json".format(str(saved_version),str(lang))
    r = requests.get(url)
    return r.json()


def get_summoner_img(img_name):
    """
    Devuelve la imagen de un summoner
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/spell/{}".format(str(saved_version),str(img_name))
    return url


# Icons
def get_all_icon_data(lang=DEF_LANG):
    """
    Devuelve la lista de iconos
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/profileicon.json".format(str(saved_version),str(lang))
    r = requests.get(url)
    return r.json()


def get_icon_img(icon):
    """
    Devuelve la url de la imagen del icono
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/img/profileicon/{}".format(str(saved_version), str(icon))
    return url


# Runes

def get_all_runes_data(lang=DEF_LANG):
    """
    Devuelve la lista de runas
    """
    saved_version = get_current_version()
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/{}/runesReforged.json".format(saved_version, lang)
    r = requests.get(url)
    return r.json()

def get_rune_img(icon_url):
    """
    Devuelve la url al icono de la runa
    """

    url = "https://ddragon.leagueoflegends.com/cdn/img/{}".format(icon_url)
    return url