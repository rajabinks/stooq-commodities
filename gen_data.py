"""
Copyright (C) 2022 J. S. Grewal <rg_public@proton.me>

Title:                  gen_data.py
Usage:                  python gen_data.py

Versioning:
    python              3.10
    black               22.10
    isort               5.10

    pandas-datareader   0.10

Description:
    Collects and cleans raw market data from online sources for further processing.
    All data is remotely (and freely) obtained using pandas-datareader
    following https://pydata.github.io/pandas-datareader/remote_data.html.

    Historical data for major indices, commodities, and currencies is obtained from
    Stooq at https://stooq.com/. Note not every symbol can be utilised, all must be
    individually checked to determine feasibility.

    Occasionally will receive "SymbolWarning: Failed to read symbol" from Stooq API,
    running the script again usually fixes this but might not probably.

Instructions:
    1. Select appropriate start and end date for data for all assets with daily data
       sampling frequency.
    2. Enter into the dictionary the obtained Stooq symbols for desired assets and
       place them in list following the naming scheme.
    3. Running file will scrape data and place it in a directory containing pickle
       and csv files, along with cleaned NumPy arrays.

Stooq - Symbols and Data Availability:
    ^SPX: S&P 500                       https://stooq.com/q/d/?s=^spx
    ^DJI: Dow Jones Industrial 30       https://stooq.com/q/d/?s=^dji
    ^NDX: Nasdaq 100                    https://stooq.com/q/d/?s=^ndx

    GC.F: Gold - COMEX                  https://stooq.com/q/d/?s=gc.f
    SI.F: Silver - COMEX                https://stooq.com/q/d/?s=si.f
    HG.F: High Grade Copper - COMEX     https://stooq.com/q/d/?s=hg.f
    PL.F: Platinum - NYMEX              https://stooq.com/q/d/?s=pl.f
    PA.F: Palladium - NYMEX             https://stooq.com/q/d/?s=pa.f

    CL.F: Crude Oil WTI - NYMEX         https://stooq.com/q/d/?s=cl.f
    RB.F: Gasoline RBOB - NYMEX         https://stooq.com/q/d/?s=rb.f

    LS.F: Lumber Random Length - CME    https://stooq.com/q/d/?s=ls.f
    LE.F: Live Cattle - CME             https://stooq.com/q/d/?s=le.f
    KC.F: Coffee - ICE                  https://stooq.com/q/d/?s=kc.f
    OJ.F: Orange Juice - ICE            https://stooq.com/q/d/?s=oj.f

    ^ = index value
    .C = cash
    .F = front month futures
"""

import os

import numpy as np
import pandas as pd
import pandas_datareader.data as pdr

from utils import dataframe_to_array, market_data_tests, single_asset_histories

"""
    ********************************************************************************
    AS OF THE TIMING OF THIS MOST RECENT COMMIT, STOOQ NO LONGER ALLOWS THE
    DOWNLOADING OF COMMODITIES DATA AND SO THEY WILL RETURN AN ERROR.
    https://github.com/pydata/pandas-datareader/issues/925
    ********************************************************************************
"""

# common starting/ending dates for daily data collection for all assets
start: str = "1985-10-01"
end: str = "2022-02-10"

# save data for all singular assets using False == 0 and True == 1
SAVE_SINGLES = 1

# fmt: off

stooq: dict = {
    # pairs for data saving and assets to be included
    # market_id: [market_name, included assets (List[str])]

    # template for creating a new bundle consisting of assets 0 -> n:
    # "mktX": ["bundle_name", ["asset_0", ..., "asset_n"]]

    "mkt0": ["snp", ["^SPX"]],

    "mkt1": ["usei", ["^SPX", "^DJI", "^NDX"]],

    "mkt2": ["dji", ["^SPX", "^DJI", "^NDX",
                     "AAPL.US", "AMGN.US", "AXP.US", "BA.US", "CAT.US", "CVX.US",
                     "DIS.US", "HD.US", "IBM.US", "INTC.US", "JNJ.US", "JPM.US",
                     "KO.US", "MCD.US", "MMM.US", "MRK.US", "MSFT.US", "NKE.US",
                     "PFE.US", "PG.US", "VZ.US", "WBA.US", "WMT.US",
                     "CSCO.US", "UNH.US",                              # starts 1990
                    #   "CRM.US", "DOW.US", "GS.US", "TRV.US", "V.US"    # very little data
                    ]],

    # unable to update commodities data from Stooq

    # "mkt3": ["minor", ["^SPX", "^DJI", "^NDX",
    #                    "GC.F", "SI.F",
    #                    "CL.F"
    #                    ]],

    # "mkt4": ["medium", ["^SPX", "^DJI", "^NDX",
    #                     "GC.F", "SI.F", "HG.F", "PL.F",
    #                     "CL.F",
    #                     "LS.F"
    #                     ]],

    # "mkt5": ["major", ["^SPX", "^DJI", "^NDX",
    #                    "GC.F", "SI.F", "HG.F", "PL.F", "PA.F",
    #                    "CL.F", "RB.F",
    #                    "LS.F", "LE.F", "KC.F", "OJ.F"
    #                    ]],

    # "mkt6": ["full", ["^SPX", "^DJI", "^NDX",
    #                   "GC.F", "SI.F", "HG.F", "PL.F", "PA.F",
    #                   "CL.F", "RB.F",
    #                   "LS.F", "LE.F", "KC.F", "OJ.F",
    #                   "AAPL.US", "AXP.US", "BA.US", "CAT.US", "CVX.US",
    #                   "DIS.US", "HD.US", "IBM.US", "INTC.US", "JNJ.US", "JPM.US",
    #                   "KO.US", "MCD.US", "MMM.US", "MRK.US", "MSFT.US", "NKE.US",
    #                   "PFE.US", "PG.US", "RTX.US", "VZ.US", "WBA.US", "WMT.US", "XOM.US"
    #                   "CSCO.US", "UNH.US",                   # starts 1990
    #                #    "DOW.US", "GS.US", "TRV.US", "V.US"    # very little data
    #                 ]],
    }

# fmt: on

if __name__ == "__main__":

    # directory for saving market prices dataframes, csvs, and arrays
    path = "./market_data/"
    # market price type (Open, High, Low, or Close)
    price_type = "Close"

    # relative directory for saving single asset price histories
    path_singles = path + "singles/"
    # market price type (Open, High, Low, or Close) for singles
    price_type_singles = "Close"

    # CONDUCT TESTS
    market_data_tests(
        start,
        end,
        SAVE_SINGLES,
        stooq,
        path,
        path_singles,
        price_type,
        price_type_singles,
    )

    if not os.path.exists(path):
        os.makedirs(path)

    for x in stooq:
        name = "stooq_" + str(stooq[str(x)][0])
        assets = stooq[str(x)][1]

        scraped_data = pdr.get_data_stooq(assets, start, end)
        scraped_data.to_pickle(path + name + ".pkl")

        market = pd.read_pickle(path + name + ".pkl")

        market.to_csv(path + name + ".csv")

        prices = dataframe_to_array(market, price_type)
        np.save(path + name + ".npy", prices)

        print(
            "{}: n_assets = {}, days = {}".format(
                name, prices.shape[1], prices.shape[0]
            )
        )

    if SAVE_SINGLES:

        if not os.path.exists(path_singles):
            os.makedirs(path_singles)

        market_1 = pd.read_pickle(path + "stooq_major.pkl")
        market_2 = pd.read_pickle(path + "stooq_dji.pkl")

        datasets = [market_1, market_2]

        for market in datasets:
            single_asset_histories(market, price_type_singles, path_singles)
