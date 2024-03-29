import streamlit as st
import pandas as pd
import requests
import time
st.set_page_config(layout="wide")
st.title("Penny Stock Data Science")
polygon_key = st.secrets["polygon_key"]


def fetch_data():
    url_naz = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
    df_naz = pd.read_csv(url_naz, delimiter="|")
    nasdaq_symbol_list = df_naz['Symbol'].dropna().tolist()
    master_list = []
    url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?include_otc=true&apiKey="+polygon_key
    #add something to get lists of otc vs listed
    response = requests.get(url)
    data = response.json()
    tickers_list = data["tickers"]
    for i in tickers_list:
        ticker = i["ticker"]
        percentage_str = i["todaysChangePerc"]
        percentage_float = float(percentage_str)
        change_str = i["todaysChange"]
        change_float = float(change_str)
        dayDic = i["day"]
        dayV = dayDic["v"]
        dayVint = int(dayV)
        dayVW = dayDic["vw"]
        dayVWfloat = float(dayVW)
        daylastTrade = i["lastTrade"]
        dayPrice = daylastTrade["p"]
        dayPriceFloat = float(dayPrice)
        dollarValue = int(dayVint*dayVWfloat)
        epoch_time = int(time.time())
        new_list = [ticker,dayPriceFloat,dayVWfloat,percentage_float,dayVint,dollarValue,epoch_time]
        master_list.append(new_list)
    columns = ["Ticker","Price","VWAP","% Change","Volume","$ Volume","Time"]
    df = pd.DataFrame(master_list, columns=columns)
    df=df[df["$ Volume"] > 5000]
    df_sorted = df.sort_values(by="% Change", ascending=False)
    df_sorted['Price'] = df_sorted['Price'].round(2)
    df_sorted['VWAP'] = df_sorted['VWAP'].round(2)
    df_sorted["% Change"] = df_sorted["% Change"].round(2)
    df_sorted["% Change"] = df_sorted["% Change"].apply(lambda x: '{:+}%'.format(x) if x >= 0 else '{:-}%'.format(x))
    naz_df = df_sorted[df_sorted["Ticker"]].isin(nasdaq_symbol_list)
    otc_df = df_sorted[~df_sorted["Ticker"]].isin(nasdaq_symbol_list)
    trip_otc_df = otc_df[otc_df['Price'] < 0.001]
    sub_otc_df = otc_df[(otc_df['Price'] >= 0.001) & (otc_df['Price'] <= 0.01)]
    penny_plus_df = otc_df[otc_df['Price'] > 0.01]

    return naz_df, trip_otc_df, sub_otc_df, penny_plus_df

def main():
    st.header('Listed')
    df1 = st.empty()
    st.header('Triple Zero')
    df2 = st.empty()
    st.header('Sub Penny')
    df3 = st.empty()    
    st.header('Penny +')
    df4 = st.empty()    

    # Infinite loop to continuously update data
    while True:
        try:
            # Fetch data from Polygon.io API
            new_df1, new_df2, new_df3, new_df4 = fetch_data()
            df1.dataframe(new_df1, hide_index=True)
            df2.dataframe(new_df2, hide_index=True)
            df3.dataframe(new_df3, hide_index=True)
            df4.dataframe(new_df4, hide_index=True)
            # Sleep for 1 second before making the next API call
            time.sleep(.1)

        except Exception as e:
            continue

# Run the Streamlit app
if __name__ == '__main__':
    main()