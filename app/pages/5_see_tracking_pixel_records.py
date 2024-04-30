import pandas as pd
import requests
import streamlit as st
from datetime import datetime, timezone

from utils import display_sidebar


def get_current_time_for_filenames():
  return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S_%f")


# Fetch the data for tabular display from the API endpoint
def fetch_visitor_records(url):
  domain = f'https://{url}' if 'https://' not in url else url
  response = requests.get(f"{domain}/logs", params={'path': 'px'})
  return response.json()


# Define the response in a tabular fashion
def display_records(data):
  if data:
    # Transform the data from the API to a Dataframe
    count = data.get('count', 0)
    st.write(f'Number of visits recorded as of now: {count}')
    df = pd.DataFrame(data['records']) if data.get('records', None) else None
    # Display the DataFrame using streamlist
    # Add download button to download DataFrame as CSV
    if df is not None:
      # Display the DataFrame using Streamlit
      tabular_data = st.dataframe(data=df, use_container_width=True)

      # Add download button to download DataFrame as CSV
      csv = df.to_csv(index=False)
      file_ts = get_current_time_for_filenames()
      st.download_button(
        label="Download CSV file",
        data=csv, file_name=f"pixel_logs_{file_ts}.csv", mime="text/csv")
      return tabular_data
    else:
      st.error("The given short URL record was not found")
  else:
    return st.warning("There is currently no data to display")


def main():
  secrets = st.secrets
  host = secrets['host']
  st.set_page_config(page_title="Tracking pixel records", layout="wide")
  display_sidebar()
  st.header("Visitor logs for tracking pixel")
  # secret_key = st.text_input(
  #   label='Secret key',
  #   help='Enter the value for the secret key for authentication',
  #   type="password",
  #   value=params.get('secret_key') if params else None)
  submit_btn = st.button(label='Fetch logs')

  if submit_btn:
    st.divider()
    try:
      request = fetch_visitor_records(host)
      display_records(request)
    except (ConnectionError, Exception) as e:
      st.error(f"{str(e)}")


if __name__ == '__main__':
  main()
