import concurrent.futures
import time
from threading import Lock

import numpy as nm
import pandas as pd
import requests


class Items:
    def __init__(self, itemIds, region="10000002"):
        """
        Default Region: The Forge
        """

        self.region = region
        self.itemIds = itemIds
        self.ItemInfoList = []

        self.dfItemInfo = pd.DataFrame()
        # self.dfItemInfoList = []

    # will run in Threads
    def ItemInfo(self, itemId):
        """
        itemId = List of max len 200
        """

        idS = str(itemId)[1:-1].replace(" ", "")

        # NO Region
        # URL = f"https://api.evemarketer.com/ec/marketstat/json?typeid={idS}"

        # With Region
        URL = f"https://api.evemarketer.com/ec/marketstat/json?typeid={idS}&regionlimit={self.region}"

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
            "Accept-Language": "en-US;q=0.9",
        }
        res = requests.get(URL, headers=HEADERS)

        with lock:
            # print(res)
            # print(len(res.json()))
            # print("\n\n")
            self.ItemInfoList.extend(res.json())

    def chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i : i + n]

    def runThreading(self, MAX_THREADS):
        itemIdsChunks = list(self.chunks(self.itemIds, 199))

        threads = min(MAX_THREADS, len(itemIdsChunks))
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.ItemInfo, itemIdsChunks)

    def runThreadingForFinalList(self, threads):
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.makeItemInfoDF, self.ItemInfoList)

    # will run in Threads
    def makeItemInfoDF(self, itemInfoJSON):
        """send Item info JSON from JSON list"""

        a = itemInfoJSON
        ItemID = a["buy"]["forQuery"]["types"][0]
        ItemName = dfTypeids.loc[dfTypeids["0"] == ItemID].values[0][1]

        sellPercentile = a["sell"]["fivePercent"]
        sellMin = a["sell"]["min"]
        sellAvg = a["sell"]["wavg"]
        buyPercentile = a["buy"]["fivePercent"]
        buyMax = a["buy"]["max"]
        buyAvg = a["buy"]["wavg"]

        # Buy/Sell Avg Deff [wavg]
        df = pd.Series([buyAvg, buyPercentile]).pct_change() * 100
        # buyAvgDiff = format(df.values[1], ".3f")
        buyAvgDiff = df.values[1]

        df = pd.Series([sellAvg, sellPercentile]).pct_change() * 100
        # sellAvgDiff = format(df.values[1], ".3f")
        sellAvgDiff = df.values[1]

        # Percentile Diff
        df = pd.Series([buyPercentile, sellPercentile]).pct_change() * 100
        # percenDiff = format(df.values[1], ".3f")
        percenDiff = df.values[1]

        if nm.isfinite(percenDiff) and percenDiff > 10:
            URL = f"https://esi.evetech.net/latest/markets/{self.region}/history/?datasource=tranquility&type_id={ItemID}"

            HEADERS = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36",
                "Accept-Language": "en-US;q=0.9",
            }
            res = requests.get(URL, headers=HEADERS)

            if res.ok and res.json():
                m13 = res.json()[-13:]

                # avgPrice13 = 0
                avgOrder13 = 0
                avgVolume13 = 0
                for m in m13:
                    # avgPrice13 += m['average']
                    avgOrder13 += m["order_count"]
                    avgVolume13 += m["volume"]

                # avg order count in 13 days
                # avgOrder13 = format(avgOrder13/13, ".3f")
                avgOrder13 = avgOrder13 / 13

                # Stop if Order count is less then 300/day
                # if avgOrder13 < 299:
                #   return

                # sell price avg last 13 day
                # avgPrice13 = format(avgPrice13/13, ".3f")

                # inc/dec last 13 day
                # priceDiff13 = m13[-1]['average'] - m13[0]['average']
                # priceDiff13 = format(priceDiff13, ".3f")

                # inc/dec last 13 day in Percent
                df = (
                    pd.Series([m13[0]["average"], m13[-1]["average"]]).pct_change()
                    * 100
                )
                priceDiffPercnt13 = format(df.values[1], ".3f")

                # avg sell volume
                # avgVolume13 = format(avgVolume13/13, ".3f")
                avgVolume13 = avgVolume13 / 13

                # Latest date for market history
                latestDate = m["date"]

                # with lock:
                #   print("Before Dict\n")
                #   print(type(percenDiff))
                #   print(percenDiff)
                #   print(sellAvgDiff)
                #   print(buyAvgDiff)
                #   print("\n\n\n")

                try:
                    dict1 = {
                        "Item Name": ItemName,
                        "Buy/Sell Diff (%)": round(percenDiff),
                        # Competition
                        "Order Count [13 days Avg]": round(avgOrder13),
                        "Items per Order [13 days Avg]": round(
                            float(avgVolume13) / float(avgOrder13)
                        ),
                        "Total Sell Volume [13 days Avg]": round(avgVolume13),
                        "Sell Avg Diff (%)": round(sellAvgDiff),
                        "Buy Avg Diff (%)": round(buyAvgDiff),
                        "Profit Prt Unit": sellPercentile - buyPercentile,
                        "Sell": sellPercentile,
                        "Buy": buyPercentile,
                        # 'Avg Price [13 days]' : avgPrice13,
                        "Price Diff (%) [from 13 day]": priceDiffPercnt13,
                        # 'Price Diff [13 day]' : priceDiff13,
                        "Sell Min": sellMin,
                        "Buy Max": buyMax,
                        "ItemID": format(ItemID, ".0f"),
                        "latest Date [Market History]": "D: " + str(latestDate),
                    }
                except Exception as e:
                    with lock:
                        # print(type(percenDiff))
                        print(percenDiff)
                        print(avgOrder13)
                        print(avgVolume13)
                        print(sellAvgDiff)
                        print(buyAvgDiff)
                        print(e)
                        print(ItemName, "\n\n")

                        # print( e, "\nDict failed")

                # with lock:
                #   print("After Dict\n")
                with lock:
                    # print("self.dfItemInfoList.append(dict)")
                    # self.dfItemInfoList.append(dict1)
                    self.dfItemInfo = self.dfItemInfo.append(dict1, ignore_index=True)

    def start(self, evemerketerThreads=99, evetechThreads=99):
        """Default Thread count 99 for All"""

        t0 = time.time()
        print("\n\nPlease wait a Moment...")
        self.runThreading(evemerketerThreads)
        print("-->Time Taken: ", time.time() - t0)

        t1 = time.time()
        print("\nMaking Final list with Threading...")
        self.runThreadingForFinalList(evetechThreads)

        print("-->Time Taken: ", time.time() - t1, "\n\n")

        print("D O N E")
        print("-->Total Time Taken: ", time.time() - t0, "\n\n")

        # return self.ItemInfoList
        # return self.ItemInfoList
        print("Total items after web Request: ", len(self.ItemInfoList))
        print("Final list: ", len(self.dfItemInfo), "\n\n")
        # print("dfItemInfoList: ", len(self.dfItemInfoList), '\n\n\n')


# if __name__ == "__main__":
print("Starting...")

print("Collecting All ItemsID and Names...")
dfTypeids = pd.read_csv("http://www.fuzzwork.co.uk/resources/typeids.csv")
itemIds = list(dfTypeids["0"].values)
print(f"-->Total items to Check: {len(itemIds)}")

lock = Lock()

itemsInfo = Items(itemIds[:5000])

itemsInfo.start(199, 37)
