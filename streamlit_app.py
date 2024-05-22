import streamlit as st
import pandas as pd
import requests
import time
import math
st.set_page_config(layout="wide")
#st.title("Penny Stock Data Science")
#test

polygon_key = st.secrets["polygon_key"]

# Define a function to apply bold style
def bold_style(val):
    return 'font-weight: bold'

# Define a function to apply green style
def green_style(val):
    return 'color: green'

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
        cont_list = ["Q","D"]
        if len(ticker) == 5 and ticker[-1] not in cont_list:
            continue
        if "." in ticker or ticker != ticker.upper():
            continue
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
        #new_list = [ticker,dayPriceFloat,dayVWfloat,percentage_float,dayVint,dollarValue,loc,epoch_time]
        new_list = [ticker,dayPriceFloat,dayVWfloat,percentage_float,dayVint,dollarValue,loc]
        master_list.append(new_list)
    #columns = ["Ticker","Price","VWAP","% Change","Volume","$ Volume","Venue","Time"]
    columns = ["Ticker","Price","VWAP","% Change","Volume","$ Volume","Venue"]
    df = pd.DataFrame(master_list, columns=columns)
    #df=df[df["$ Volume"] > 5000]
    df_sorted = df.sort_values(by="% Change", ascending=False)
    df_sorted["% Change"] = df_sorted["% Change"].round(2)
    df_sorted["% Change"] = df_sorted["% Change"].apply(lambda x: '{:+}%'.format(x) if x >= 0 else '{:-}%'.format(x))
    naz_df = df_sorted[df_sorted['Venue'] == 'listed']
    naz_df = naz_df[naz_df['Price'] < 100].head(75)
    naz_df = naz_df.drop(columns=['Venue'])
    #naz_df['Price'] = naz_df['Price'].round(2)
    #naz_df['VWAP'] = naz_df['VWAP'].round(2)
    otc_df = df_sorted[df_sorted['Venue'] == 'otc']
    otc_df = otc_df[otc_df["$ Volume"] > 5000]
    otc_df = otc_df.drop(columns=['Venue'])
    trip_otc_df = otc_df[otc_df['Price'] < 0.001].head(50)
    #trip_otc_df = trip_otc_df.drop(columns=['Venue'])
    sub_otc_df = otc_df[(otc_df['Price'] >= 0.001) & (otc_df['Price'] <= 0.01)].head(50)
    #sub_otc_df = sub_otc_df.drop(columns=['Venue'])
    penny_plus_df = otc_df[otc_df['Price'] > 0.01].head(50)
    #penny_plus_df = penny_plus_df.drop(columns=['Venue'])

    # Apply the styles to column 'Ticker' and all headers
    #naz_df = naz_df.style.applymap(bold_style, subset=pd.IndexSlice[:, 'Ticker']).apply(bold_style, axis=1)
    #trip_otc_df = trip_otc_df.style.applymap(bold_style, subset=pd.IndexSlice[:, 'Ticker']).apply(bold_style, axis=1)
    #sub_otc_df = sub_otc_df.style.applymap(bold_style, subset=pd.IndexSlice[:, 'Ticker']).apply(bold_style, axis=1)
    #penny_plus_df = penny_plus_df.style.applymap(bold_style, subset=pd.IndexSlice[:, 'Ticker']).apply(bold_style, axis=1)

    # Apply green style to selected columns
    #naz_df = naz_df.applymap(green_style, subset=['Price', 'VWAP', '% Change'])
    #trip_otc_df = trip_otc_df.applymap(green_style, subset=['Price', 'VWAP', '% Change'])
    #sub_otc_df = sub_otc_df.applymap(green_style, subset=['Price', 'VWAP', '% Change'])
    #penny_plus_df = penny_plus_df.applymap(green_style, subset=['Price', 'VWAP', '% Change'])

    return naz_df, trip_otc_df, sub_otc_df, penny_plus_df

def main():
    # First row with two columns
    columns_row1 = st.columns(2)
    with columns_row1[0]:
        st.markdown('**Listed**')
        df1 = st.empty()
    with columns_row1[1]:
        st.markdown('**Triple Zero**')
        df2 = st.empty()
    
    # Second row with two columns
    columns_row2 = st.columns(2)
    with columns_row2[0]:
        st.markdown('**Sub Penny**')
        df3 = st.empty()
    with columns_row2[1]:
        st.markdown('**Penny +**')
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
            time.sleep(1)

        except Exception as e:
            continue

# Run the Streamlit app
if __name__ == '__main__':
    main()