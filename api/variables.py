from django.conf import settings

GRIETA = {
    "name":"Summoner's Rift",
    "mapId":"11"
}

ARAM = {
    "name":"Howling Abyss",
    "mapId":"12"
}

MAIN_GAMEMODE="CLASSIC"
GAME_TYPE="MATCHED_GAME"

DIVISIONS=["I","II","III","IV"]
TIERS=["DIAMOND","PLATINUM","GOLD","SILVER","BRONZE","IRON"]

TOKEN_HEADER={
    "X-Riot-Token": settings.API_KEY
}

SERVER_ROUTES={
    "LAS":"la2.api.riotgames.com",
    "LAN":"la1.api.riotgames.com",
    "KR":"kr.api.riotgames.com",
    "JP":"jp1.api.riotgames.com",
    "BR":"br1.api.riotgames.com",
    "NA":"na1.api.riotgames.com",
    "EUN":"eun1.api.riotgames.com",
    "EUW":"euw1.api.riotgames.com",
    "OC":"oc1.api.riotgames.com",
    "TR":"tr1.api.riotgames.com",
    "RU":"ru.api.riotgames.com"
}

RANKED_QUEUES=[420]

SERVER_REAL_NAME_TO_ROUTE={
    "BR1":"BR",
    "EUN1":"EUN",
    "EUW1":"EUW",
    "JP1":"JP",
    "KR":"KR",
    "LA1":"LAN",
    "LA2":"LAS",
    "OC1":"OC",
    "TR1":"TR",
    "RU":"RU",
    "NA1":"NA",
}


MATCHES_STATS_KEYS=[
    "win","item0","item1","item2","item3","item4","item5","item6","kills","deaths","assists","pentaKills","quadraKills","doubleKills","tripleKills","totalDamageDealtToChampions","magicDamageDealtToChampions","physicalDamageDealtToChampions","perk0","perk1","perk2","perk3","perk4","perk5","perkPrimaryStyle","perkSubStyle","statPerk0","statPerk1","statPerk2"
]

PLAYSTYLE_STATS_KEYS = [
    "win","kills","assists","deaths","totalDamageDealtToChampions","magicDamageDealtToChampions","physicalDamageDealtToChampions","goldEarned","totalMinionsKilled","neutralMinionsKilled","neutralMinionsKilledTeamJungle","neutralMinionsKilledEnemyJungle","wardsPlaced","wardsKilled",
]