import requests

from .variables import DIVISIONS, TIERS, TOKEN_HEADER, SERVER_ROUTES, RANKED_QUEUES


def get_data_or_none(url):
    """
    Hace un get a una url, si el status no es 200 retorna None
    """
    r = requests.get(url, headers=TOKEN_HEADER)
    if r.status_code==200:
        return r.json()

    return None


# Player
def get_player_by_name(name, region):
    """
    Devuelve la informacion de un jugador segun su nick
    y region, retorna None si no se encuentra
    """
    url = "https://{}/lol/summoner/v4/summoners/by-name/{}".format(SERVER_ROUTES[region], str(name))
    return get_data_or_none(url)


# Matches
def get_current_match_by_player_id(id, region):
    """
    Devuelve la informacion de la partida actual
    segun su encrypted id y region, si no esta en partida
    retorna None
    """

    url = "https://{}/lol/spectator/v4/active-games/by-summoner/{}".format(SERVER_ROUTES[region], str(id))
    return get_data_or_none(url)


def get_match_by_id(id, region):
    """
    Devuelve los datos de una partida finalizada por su id,
    o none si no la encuentra
    """

    url = "https://{}/lol/match/v4/matches/{}".format(SERVER_ROUTES[region], str(id))
    return get_data_or_none(url)


def get_matchlist_by_account_id(id, region, only_ranked=False):
    """
    Devuelve la matchlist de un summoner segun su account id,
    o None si no lo encuentra
    """

    url = "https://{}/lol/match/v4/matchlists/by-account/{}".format(SERVER_ROUTES[region], str(id))
    if only_ranked:
        url+="?"
        for x in RANKED_QUEUES:
            url+="&queue="+str(x)
    
    response = get_data_or_none(url)
    if response is None:
        return None
    return response['matches']


# Masteries
def get_champ_masteries_by_player_id(id,region):
    """
    Devuelve la lista de champs con su maestria descendente,
    segun el id del jugador, o None si no lo encuentra
    """

    url = "https://{}/lol/champion-mastery/v4/champion-masteries/by-summoner/{}".format(SERVER_ROUTES[region], str(id))
    return get_data_or_none(url)


# Leagues
def get_leagues_by_player_id(id, region):
    """
    Devuelve la lista de ligas de un jugador, si es unranked
    devuelve una lista vacia
    """

    url = "https://{}/lol/league/v4/entries/by-summoner/{}".format(SERVER_ROUTES[region], str(id))
    return get_data_or_none(url)


def get_player_list_by_division(tier,division,region):
    """
    Devuelve el top 100 de jugadores para una division en una liga
    """

    if tier not in TIERS or division not in DIVISIONS:
        return None

    url = "https://{}/lol/league/v4/entries/RANKED_SOLO_5x5/{}/{}?page=1".format(SERVER_ROUTES[region],tier,division)
    return get_data_or_none(url)


def get_player_list_challenger(region):
    """
    Devuelve top 100 de jugadores en challenger
    """

    url = "https://{}/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5".format(SERVER_ROUTES[region])
    return get_data_or_none(url)


def get_player_list_grandmaster(region):
    """
    Devuelve top 100 de jugadores en grandmaster
    """

    url = "https://{}/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5".format(SERVER_ROUTES[region])
    return get_data_or_none(url)


def get_player_list_master(region):
    """
    Devuelve top 100 de jugadores en master
    """

    url = "https://{}/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5".format(SERVER_ROUTES[region])
    return get_data_or_none(url)


