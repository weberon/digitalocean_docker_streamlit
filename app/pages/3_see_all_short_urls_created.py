import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timezone
from utils import display_sidebar
from st_aggrid import GridOptionsBuilder, AgGrid, ColumnsAutoSizeMode


# Function to fetch data from API endpoint with caching
@st.cache_data
def fetch_data(url, params):
  domain = f'https://{url}' if 'https://' not in url else url
  response = requests.get(f"{domain}/records", params=params)
  return response.json()


def fetch_short_url_stats(url, params):
  domain = f'https://{url}' if 'https://' not in url else url
  response = requests.get(f"{domain}/logs", params=params)
  return response.json()


def generate_aggrid(df):
  gb = GridOptionsBuilder.from_dataframe(df)
  gb.configure_selection(selection_mode="single")
  gb.configure_grid_options(domLayout='wide')
  go = gb.build()

  grid_response = AgGrid(
    df,
    gridOptions=go,
    width="100%",
    enable_enterprise_modules=False,
    fit_columns_on_grid_load=True,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
  )
  if 'selected_rows' in st.session_state:
    st.session_state.selected_rows = grid_response['selected_rows']
  return grid_response


# Function to get current time for filenames
def get_current_time_for_filenames():
  return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S_%f")


# Function to display records
def display_records(data):
  if data:
    count = data.get('count', 0)
    if count != 0:
      st.write(f'Number of short urls created by you, as of now: {count}')
    df = pd.DataFrame(data['records']) if data.get('records', None) else None
    if df is not None:
      csv = df.to_csv(index=False)
      file_ts = get_current_time_for_filenames()
      st.download_button(
          label="Download CSV file",
          data=csv, file_name=f"short_urls_{file_ts}.csv", mime="text/csv")
      return df
    else:
      st.error("You are yet to create any short url records")
  else:
    return st.warning("There is currently no data to display")


def main():
  secrets = st.secrets
  host = secrets['host']

  # Initialize session state
  if 'secret_key' not in st.session_state:
    st.session_state.secret_key = None
  if 'selected_rows' not in st.session_state:
    st.session_state.selected_rows = None

  st.set_page_config(
      page_title="List of short URLs created by a user",
      layout="wide"
  )
  display_sidebar()
  st.title("Short URL records created by a user")

  secret_key = st.text_input(
    label='Your assigned secret key',
    help='Enter the value for the secret key assigned to you',
    placeholder='For ex: abcDeFgh!@',
    type='password',
    value=st.session_state.secret_key
  )
  st.session_state.secret_key = secret_key
  submit_btn = st.button(label='Fetch your short URLs')

  if submit_btn:
    st.divider()
    if not secret_key:
      st.error("Value for secret key cannot be empty")
    else:
      st.subheader("Results")
      try:
        request = fetch_data(
            host,
            {'secret_key': secret_key}
        )
        df = display_records(request)
        if df is not None:
          # Only update the DataFrame if the data has changed
          if 'df' not in st.session_state or not df.equals(st.session_state.df):
            st.session_state.df = df

      except (ConnectionError, Exception) as e:
        st.error(f"{str(e)}")

  # st.code(st.session_state)

  # Render the AgGrid outside of the if submit_btn: block
  if 'df' in st.session_state:
    generate_aggrid(st.session_state.df)
  if st.session_state.selected_rows is None:
    st.warning("No short url record is selected yet.")
  else:
    selected_row = st.session_state.selected_rows
    if selected_row is None:
      return st.warning("Please select any one row to view statistics")
    else:
      try:
        params = {'secret_key': secret_key, 'path': selected_row["short_url"]}
        response = fetch_short_url_stats(host, params)
        if response['count'] == 0:
          return st.error('The selected short url does not have any visits yet')
        else:
          return st.dataframe(response['records'])
      except KeyError:
        print(selected_row)


if __name__ == '__main__':
  main()
