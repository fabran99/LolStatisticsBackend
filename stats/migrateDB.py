from stats.models import *

from lol_stats_api.helpers.mongodb import get_mongo_players, get_mongo_stats

db_players = get_mongo_players()
db_stats = get_mongo_stats()


def migratePlayers():
    cursor = db_players.player_list.find()

    playerList = []
    for x in cursor:
        player = x.copy()
        del player['_id']
        playerList.append(Player(**player))

        if len(playerList) % 100 == 0:
            print("Insertando jugadores")
            Player.objects.bulk_create(playerList)
            playerList = []

    if len(playerList) > 0:
        Player.objects.bulk_create(playerList)


def migrateTimelines():
    cursor = db_stats.timelines.find()

    timelineList = []
    for x in cursor:
        timeline = x.copy()
        del timeline['_id']
        timelineList.append(Timeline(**timeline))

        if len(timelineList) % 100 == 0:
            print("Insertando timeline")
            Timeline.objects.bulk_create(timelineList)
            timelineList = []

    if len(timelineList) > 0:
        Timeline.objects.bulk_create(timelineList)


def migrateBans():
    cursor = db_stats.bans.find()

    banList = []
    for x in cursor:
        ban = x.copy()
        del ban['_id']
        banList.append(Ban(**ban))

        if len(banList) % 100 == 0:
            print("Insertando ban")
            Ban.objects.bulk_create(banList)
            banList = []

    if len(banList) > 0:
        Ban.objects.bulk_create(banList)


def migrateTimelines():
    cursor = db_stats.timelines.find()

    timelinesList = []
    for x in cursor:
        timeline = x.copy()
        del timeline['_id']
        timelinesList.append(Timeline(**timeline))

        if len(timelinesList) % 100 == 0:
            print("Insertando timelines")
            Timeline.objects.bulk_create(timelinesList)
            timelinesList = []

    if len(timelinesList) > 0:
        Timeline.objects.bulk_create(timelinesList)


def migrateFirstBuy():
    cursor = db_stats.first_buy.find()

    fbList = []
    for x in cursor:
        firstbuy = x.copy()
        del firstbuy['_id']
        fbList.append(FirstBuy(**firstbuy))

        if len(fbList) % 100 == 0:
            print("Insertando first buys")
            FirstBuy.objects.bulk_create(fbList)
            fbList = []

    if len(fbList) > 0:
        FirstBuy.objects.bulk_create(fbList)


def migrateSkillUp():
    cursor = db_stats.skill_up.find()

    skupList = []
    changedKeys = [str(i) for i in range(1, 19)]

    for x in cursor:
        skup = x.copy()
        del skup['_id']
        parsedskup = {}

        for key, value in skup.items():
            k = key
            if key in changedKeys:
                k = "_"+str(key)

            parsedskup[k] = value

        skupList.append(SkillUp(**parsedskup))

        if len(skupList) % 100 == 0:
            print("Insertando first buys")
            SkillUp.objects.bulk_create(skupList)
            skupList = []

    if len(skupList) > 0:
        SkillUp.objects.bulk_create(skupList)


def migrateChampData():
    cursor = db_stats.champ_data.find()

    champDataList = []
    for x in cursor:
        champData = x.copy()
        del champData['_id']
        del champData['kills']
        del champData['assists']
        del champData['deaths']

        if not 'perkSubStyle' in champData or champData['perkSubStyle'] is None:
            continue
        champDataList.append(ChampData(**champData))

        if len(champDataList) % 100 == 0:
            print("Insertando champ data")
            try:
                ChampData.objects.bulk_create(champDataList)
            except Exception as e:
                print(e)
            champDataList = []

    if len(champDataList) > 0:
        ChampData.objects.bulk_create(champDataList)


def migrateChampPlaystyle():
    cursor = db_stats.champ_playstyle.find()

    for x in cursor:
        champData = x.copy()
        del champData['_id']
        print("Insertando champ playstyle")

        try:
            ChampPlaystyle.objects.create(**champData)
        except Exception as e:
            print(e)
