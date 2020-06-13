import math


def GetEloName(elo):
    tiers = {
        "Diamond": 2000,
        "Platinum 5": 1936, "Platinum 4": 1872,
        "Platinum 3": 1808, "Platinum 2": 1744,
        "Platinum 1": 1680, "Platinum 0": 1622,
        "Gold 5": 1621, "Gold 4": 1564,
        "Gold 3": 1506, "Gold 2": 1448,
        "Gold 1": 1390, "Gold 0": 1338,
        "Silver 5": 1337, "Silver 4": 1386,
        "Silver 3": 1234, "Silver 2": 1182,
        "Silver 1": 1130, "Silver 0": 1086,
        "Bronze 5": 1085, "Bronze 4": 1042,
        "Bronze 3": 998, "Bronze 2": 954,
        "Bronze 1": 910, "Bronze 0": 872,
        "Tin 5": 871, "Tin 4": 834,
        "Tin 3": 796, "Tin 2": 758,
        "Tin 1": 720, "Tin 0": 200,
    }

    return next(name for name, x in tiers.items() if elo >= x)


def GetGloryFromWins(totalwins: int):
    if totalwins <= 150:
        return 20 * totalwins
    return round((10 * (45 * math.pow(math.log10(totalwins * 2), 2))) + 245)


def GetGloryFromBestRating(bestrating: int):
    retval = 0
    if (bestrating < 1200):
        retval = 250
    if (bestrating >= 100 and bestrating > 1286):
        retval = 10 * (25 + ((0.872093023) * (86 - (1286 - bestrating))))
    if (bestrating >= 1286 and bestrating < 1390):
        retval = 10 * (100 + ((0.721153846) * (104 - (1390 - bestrating))))
    if (bestrating >= 1390 and bestrating < 1680):
        retval = 10 * (187 + ((0.389655172) * (290 - (1680 - bestrating))))
    if (bestrating >= 1680 and bestrating < 2000):
        retval = 10 * (300 + ((0.428125) * (320 - (2000 - bestrating))))
    if (bestrating >= 2000 and bestrating < 2300):
        retval = 10 * (437 + ((0.143333333) * (300 - (2300 - bestrating))))
    if (bestrating >= 2300):
        retval = 10 * (480 + ((0.05) * (400 - (2700 - bestrating))))
    return round(retval)


def GetHeroEloFromOldElo(elo: int):
    if elo < 2000:
        return round((elo + 375) / 1.5)
    return round(1583 + (elo - 2000) / 10)


def GetPersonalEloFromOldElo(elo: int):
    if elo >= 1400:
        return round(1400 + (elo - 1400) / (3.0 - (3000 - elo) / 800))
    return elo
