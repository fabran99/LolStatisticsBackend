from lol_stats_api.helpers.mongodb import get_saved_version, get_last_calculated_patch
from lol_stats_api.helpers.mongodb import get_mongo_assets, get_mongo_stats, get_saved_version
from rest_framework.response import Response
from django.http import JsonResponse

assetsDb = get_mongo_assets()
statsDb = get_mongo_stats()


def get_main_list():
    patch = get_last_calculated_patch()
    img_link_dict = {
        "champ_splashart": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/$champ_key$_$skin_id$.jpg",
        "champ_square": "https://ddragon.leagueoflegends.com/cdn/{}/img/champion/$champ_key$.png".format(patch),
        "champ_loading": "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/$champ_key$_$skin_id$.jpg".format(patch),
        "item_img": "https://ddragon.leagueoflegends.com/cdn/{}/img/item/$item_id$.png".format(patch),
        "icon_img": "https://ddragon.leagueoflegends.com/cdn/{}/img/profileicon/$icon_id$.png".format(patch),
        "spell_img": "https://ddragon.leagueoflegends.com/cdn/{}/img/spell/$spell_id$.png".format(patch)
    }
    # champs
    champ_dict = {
        "name": 1,
        "title": 1,
        "tags": 1,
        "key": 1,
        "lore": 1,
        "id": 1,
        "allytips": 1,
        "enemytips": 1
    }

    stats_dict = {
        'stats.high_elo.winRate': 1,
        'stats.high_elo.pickRate': 1,
        'stats.high_elo.banRate': 1,
        'stats.high_elo.damage': 1,
        'stats.high_elo.kda.deaths': 1,
        'stats.high_elo.kda.assists': 1,
        'stats.high_elo.kda.kills': 1,
        'stats.high_elo.farmPerMin': 1,
        'stats.high_elo.farmPerMin': 1,
        'stats.high_elo.damageTypes': 1,
        'runes': 1,
        'build': 1,
        "championId": 1,
        "lanes": 1,
        "spells": 1,
        'champName': 1,
        'strongAgainst': 1,
        "weakAgainst": 1,
        "skill_order": 1,
        "info_by_lane": 1,
        "phases_winrate": 1
    }

    champ_list = {}
    ranking = {
        "ADC": {
            "winRate": 0,
            "championId": 0
        },
        "Top": {
            "winRate": 0,
            "championId": 0
        },
        "Jungla": {
            "winRate": 0,
            "championId": 0
        },
        "Mid": {
            "winRate": 0,
            "championId": 0
        },
        "Support": {
            "winRate": 0,
            "championId": 0
        }
    }

    champ_cursor = assetsDb.champ.find({}, champ_dict)
    stats_cursor = statsDb.stats_by_champ.find({'patch': patch}, stats_dict)

    for champ in champ_cursor:
        champ_list[champ['key']] = {
            "name": champ['name'],
            "title": champ['title'],
            "tags": champ['tags'],
            'key': champ['id'],
            'lore': champ['lore'],
            'allyTips': champ['allytips'],
            'enemyTips': champ['enemytips'],
        }
    for stat in stats_cursor:
        if not str(stat['championId']) in champ_list:
            continue

        high_elo_winrate = stat['stats']['high_elo']['winRate']
        lanes = stat['lanes']
        for lane in lanes:
            winrate = next(item['winRate']
                           for item in high_elo_winrate if item['lane'] == lane)

            if ranking[lane]['winRate'] < winrate:
                ranking[lane]["winRate"] = winrate
                ranking[lane]['championId'] = stat['championId']
                ranking[lane]['champName'] = stat["champName"]

        champ_list[str(stat['championId'])].update({
            "lanes": lanes,
            "winRate": stat['stats']['high_elo']['winRate'],
            "pickRate": stat['stats']['high_elo']['pickRate'],
            "banRate": stat['stats']['high_elo']['banRate'],
            "banRate": stat['stats']['high_elo']['banRate'],
            "damage": stat['stats']['high_elo']['damage'],
            "farmPerMin": stat['stats']['high_elo']['farmPerMin'],
            "deaths": stat['stats']['high_elo']['kda']['deaths'],
            "assists": stat['stats']['high_elo']['kda']['assists'],
            "kills": stat['stats']['high_elo']['kda']['kills'],
            "farmPerMin": stat['stats']['high_elo']['farmPerMin'],
            "damageTypes": stat['stats']['high_elo']['damageTypes'],
            "info_by_lane": stat["info_by_lane"],
            "strongAgainst": stat['strongAgainst'],
            "weakAgainst": stat['weakAgainst'],
            "skill_order": stat['skill_order'],
            "phases_winrate": stat['phases_winrate'],
        })

    final_list = []
    for key in champ_list.keys():
        new_obj = champ_list[key]
        new_obj['championId'] = key
        final_list.append(new_obj)

    # Runas
    rune_list = []
    perk_list = []
    rune_cursor = assetsDb.rune.find({})
    for rune in rune_cursor:
        rune.pop("_id")
        rune_list.append(rune)

    # Perks
    perks_cursor = assetsDb.perk.find({})
    for perk in perks_cursor:
        perk.pop("_id")
        perk_list.append(perk)

    version = get_last_calculated_patch()
    if not version:
        version = None

    # Items
    item_list = []
    cursor = assetsDb.item.find({}, {
        "_id": 0,
        "id": 1,
        "name": 1,
        "description": 1,
        "price": 1,
        "tags": 1
    })
    for x in cursor:
        item_list.append(x)

    # Sums
    spell_list = []
    cursor = assetsDb.summ.find({}, {
        "_id": 0,
        "id": 1,
        "name": 1,
        "description": 1,
        "cooldown": 1,
        "key": 1
    })
    for x in cursor:
        spell_list.append(x)

    # radar stats
    cursor = statsDb.radar_stats.find({'patch': patch})
    radar_stat_list = []
    for x in cursor:
        radar_stat_list.append(
            {key: value for key, value in x.items() if key not in ["_id", 'date', 'patch']})

    return JsonResponse({"champions": final_list,
                         "ranking": ranking,
                         "lol_version": version,
                         "perks": perk_list,
                         "runes": rune_list,
                         "items": item_list,
                         "img_links": img_link_dict,
                         "spells": spell_list,
                         "radar_stats": radar_stat_list
                         })
