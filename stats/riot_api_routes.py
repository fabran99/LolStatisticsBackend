import requests
from time import sleep
from django.conf import settings
import random
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, get_token_header, SERVER_ROUTES, RANKED_QUEUES, SERVER_ROUTES_API_KEYS,\
    MATCHLIST_SERVER_ROUTES, SOLO_QUEUE


def get_data_or_none(url, token=None):
    """
    Hace un get a una url, si el status no es 200 retorna None
    """
    try:
        r = requests.get(url, headers=get_token_header(token=token))
        if r.status_code == 200:
            return r.json()
        else:
            print(r.json())
    except requests.exceptions.ConnectionError as e:
        if "Exception decrypting" in str(e):
            print("La token que se uso no coincide, url: ", url)
            other_tokens = [x for x in settings.API_KEYS if x != token]
            if len(other_tokens) > 0:
                token = random.choice(other_tokens)
        sleep(35)
        try:
            r = requests.get(url, headers=get_token_header(token=token))
            if r.status_code == 200:
                return r.json()
            else:
                print(r.json())
        except:
            return None

    return None


# Player
def get_player_by_name(name, region, force_token=None):
    """
    Devuelve la informacion de un jugador segun su nick
    y region, retorna None si no se encuentra
    """
    url = "https://{}/lol/summoner/v4/summoners/by-name/{}".format(
        SERVER_ROUTES[region], str(name))
    return get_data_or_none(url,token=SERVER_ROUTES_API_KEYS[region] if not force_token else force_token)


def get_player_by_id(name, region):
    """
    Devuelve la informacion de un jugador segun su encrypted id
    y region, retorna None si no se encuentra
    """
    url = "https://{}/lol/summoner/v4/summoners/{}".format(
        SERVER_ROUTES[region], str(name))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


# Matches
def get_current_match_by_player_id(id, region):
    """
    Devuelve la informacion de la partida actual
    segun su encrypted id y region, si no esta en partida
    retorna None
    """

    url = "https://{}/lol/spectator/v4/active-games/by-summoner/{}".format(
        SERVER_ROUTES[region], str(id))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_match_by_id(id, region):
    """
    Devuelve los datos de una partida finalizada por su id,
    o none si no la encuentra
    """

    url = "https://{}/lol/match/v5/matches/{}".format(
        MATCHLIST_SERVER_ROUTES[region], str(id))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_matchlist_by_account_id(id, region, only_ranked=False, endIndex=100, beginTime=None, endTime=None, force_token=None):
    """
    Devuelve la matchlist de un summoner segun su account id,
    o None si no lo encuentra
    """

    url = "https://{}/lol/match/v4/matchlists/by-account/{}?endIndex={}".format(
        SERVER_ROUTES[region], str(id), str(endIndex))
    if only_ranked:
        for x in RANKED_QUEUES:
            url += "&queue="+str(x)

    if beginTime is not None:
        url += "&beginTime="+str(beginTime)
    if endTime is not None:
        url += "&endTime="+str(endTime)

    print(url)
    response = get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region] if not force_token else force_token)
    print(response)
    if response is None:
        return None
    return response['matches']


def get_matchlist_by_puuid_id(id, region, only_ranked=False, endIndex=100, beginTime=None, endTime=None, force_token=None):
    """
    Devuelve la matchlist de un summoner segun su puuid,
    o None si no lo encuentra
    """

    url = "https://{}/lol/match/v5/matches/by-puuid/{}/ids?endIndex={}".format(
        MATCHLIST_SERVER_ROUTES[region], str(id), str(endIndex))
    if only_ranked:
        url += "&queue="+str(SOLO_QUEUE)

    if beginTime is not None:
        url += "&startTime="+str(int(beginTime/1000))
    if endTime is not None:
        url += "&endTime="+str(int(endTime/1000))

    print(url)
    response = get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region] if not force_token else force_token)
    print(response)
    if response is None:
        return None
    return response


def get_timelist_by_match_id(id, region):
    """
    Devuelve la timeline de una partida
    """
    url = "https://{}/lol/match/v5/matches/{}/timeline".format(
        MATCHLIST_SERVER_ROUTES[region], str(id))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


# Masteries
def get_champ_masteries_by_player_id(id, region):
    """
    Devuelve la lista de champs con su maestria descendente,
    segun el id del jugador, o None si no lo encuentra
    """

    url = "https://{}/lol/champion-mastery/v4/champion-masteries/by-summoner/{}".format(
        SERVER_ROUTES[region], str(id))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


# Leagues
def get_leagues_by_player_id(id, region):
    """
    Devuelve la lista de ligas de un jugador, si es unranked
    devuelve una lista vacia
    """

    url = "https://{}/lol/league/v4/entries/by-summoner/{}".format(
        SERVER_ROUTES[region], str(id))
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_player_list_by_division(tier, division, region, page="1"):
    """
    Devuelve el top 100 de jugadores para una division en una liga
    """

    if tier not in TIERS or division not in DIVISIONS:
        return None

    url = "https://{}/lol/league/v4/entries/RANKED_SOLO_5x5/{}/{}?page={}".format(
        SERVER_ROUTES[region], tier, division, page)
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_player_list_challenger(region):
    """
    Devuelve top 100 de jugadores en challenger
    """

    url = "https://{}/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5".format(
        SERVER_ROUTES[region])
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_player_list_grandmaster(region):
    """
    Devuelve top 100 de jugadores en grandmaster
    """

    url = "https://{}/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5".format(
        SERVER_ROUTES[region])
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_player_list_master(region):
    """
    Devuelve top 100 de jugadores en master
    """

    url = "https://{}/lol/league/v4/masterleagues/by-queue/RANKED_SOLO_5x5".format(
        SERVER_ROUTES[region])
    return get_data_or_none(url, token=SERVER_ROUTES_API_KEYS[region])


def get_high_elo_player_list_by_elo(elo, region):
    """
    De acuerdo al elo llama a la funcion correspondiente
    """
    if elo == "challengers":
        return get_player_list_challenger(region)
    elif elo == "masters":
        return get_player_list_master(region)
    elif elo == "grandmasters":
        return get_player_list_grandmaster(region)

    return None
