import streamlit as st
import pandas as pd
import requests
import time
st.set_page_config(layout="wide")
st.title("Penny Stock Data Science")
polygon_key = st.secrets["polygon_key"]



def fetch_data():
    if naz_count_loop < 1:
        url_naz = "http://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
        df_naz = pd.read_csv(url_naz, delimiter="|")
        nasdaq_symbol_list = df_naz['Symbol'].dropna().tolist()
    naz_count_loop = naz_count_loop + 1
    if naz_count_loop > 10000:
        naz_count_loop = 0
    master_list = []
    url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers?include_otc=true&apiKey="+polygon_key
    #add something to get lists of otc vs listed
    response = requests.get(url)
    data = response.json()
    tickers_list = data["tickers"]
    for i in tickers_list:
        ticker = i["ticker"]
        cont_list = ["Q","D"]
        #if len(ticker) == 5 and ticker[-1] not in cont_list:
        #    continue
        #if "." in ticker or ticker != ticker.upper():
        #    continue
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
        if ticker in nasdaq_symbol_list:
            loc = "listed"
        else:
            loc = "otc"
        new_list = [ticker,dayPriceFloat,dayVWfloat,percentage_float,dayVint,dollarValue,loc,epoch_time]
        #new_list = [ticker,dayPriceFloat,dayVWfloat,percentage_float,dayVint,dollarValue,loc]
        master_list.append(new_list)
    columns = ["Ticker","Price","VWAP","% Change","Volume","$ Volume","Venue","Time"]
    #columns = ["Ticker","Price","VWAP","% Change","Volume","$ Volume","Venue"]
    df = pd.DataFrame(master_list, columns=columns)
    #df=df[df["$ Volume"] > 5000]
    df_sorted = df.sort_values(by="% Change", ascending=False)
    df_sorted["% Change"] = df_sorted["% Change"].round(2)
    df_sorted["% Change"] = df_sorted["% Change"].apply(lambda x: '{:+}%'.format(x) if x >= 0 else '{:-}%'.format(x))
    naz_df = df_sorted[df_sorted['Venue'] == 'listed']
    naz_df = naz_df[naz_df['Price'] < 25].head(50)
    #naz_df['Price'] = naz_df['Price'].round(2)
    #naz_df['VWAP'] = naz_df['VWAP'].round(2)
    otc_df = df_sorted[df_sorted['Venue'] == 'otc']
    otc_df = otc_df[otc_df["$ Volume"] > 5000]
    trip_otc_df = otc_df[otc_df['Price'] < 0.001].head(50)
    sub_otc_df = otc_df[(otc_df['Price'] >= 0.001) & (otc_df['Price'] <= 0.01)].head(50)
    penny_plus_df = otc_df[otc_df['Price'] > 0.01].head(50)

    return naz_df, trip_otc_df, sub_otc_df, penny_plus_df

def main():
    columns = st.columns(4)
    with columns[0]:
        st.header('Listed')
        df1 = st.empty()
    with columns[1]:
        st.header('Triple Zero')
        df2 = st.empty()
    with columns[2]:
        st.header('Sub Penny')
        df3 = st.empty()
    with columns[3]:
        st.header('Penny +')
        df4 = st.empty()
    naz_count_loop = 0

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
            time.sleep(1)

        except Exception as e:
            continue

# Run the Streamlit app
if __name__ == '__main__':
    main()