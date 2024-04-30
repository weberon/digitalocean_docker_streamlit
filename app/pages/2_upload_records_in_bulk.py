import streamlit as st
import requests
import pandas as pd
import segno
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from os import makedirs
from io import StringIO
import csv
import json

from utils import display_sidebar

def get_current_time_for_filenames():
  return datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S_%f")

def fetch_existing_user_campaigns(host, secret_key):
  if not host:
    return None
  url = f'https://{host}' if 'https://' not in host else host
  params = {'secret_key': secret_key}
  response = requests.get(f'{url}/campaigns', params=params)
  return response.json()

def send_to_api(host, csv_data, payload):
  if not host:
    return None
  url = f'https://{host}' if 'https://' not in host else host
  response = requests.post(f'{url}/bulk', data=payload, files={'file': csv_data})
  if response.status_code == 200:
    return response.json()
  else:
    st.error(response.text)
    return None

def generate_qr_codes(dataframe):
  qr_path = tempfile.mktemp()
  makedirs(qr_path)
  for ind, rec in enumerate(dataframe.itertuples(index=False), 1):
    trackableurl_index = dataframe.columns.get_loc('o.rp.trackableurl')
    qrcode_img_index = dataframe.columns.get_loc('o.rp.qrcode_img')
    if rec[trackableurl_index] == 'Error':
      continue
    else:
      out_path = "{}/{}".format(qr_path, rec[qrcode_img_index])
      segno.make_qr(rec[trackableurl_index]).save(out_path, scale=10, border=1)
  shutil.make_archive("qrcodes", "zip", qr_path)

def main():
  secrets = st.secrets
  state = st.session_state
  host = secrets[state.group]["HOST"]
  secret_key = secrets[state.group]["SECRET_KEY"]

  if 'trackable_urls' not in st.session_state:
    st.session_state['trackable_urls'] = None
  if 'selected_campaign' not in st.session_state:
    st.session_state['selected_campaign'] = None

  st.set_page_config(page_title="Bulk data uploader", layout="wide")
  display_sidebar()
  st.title("CSV Uploader to generate short urls and QR codes in bulk")

  if secret_key:
    available_campaigns = fetch_existing_user_campaigns(host, secret_key)
    if not available_campaigns.get('message'):
      st.write(f"You currently have {available_campaigns.get('count')} campaigns")
      with st.expander("Click here to view existing campaigns"):
        st.dataframe(
          data=available_campaigns['records'],
          column_order=("name", "destination_url", "total", "timestamp"),
          column_config={
            'customer_id': None,
            'total': 'contacts'
          }
        )
      campaign_dict = {record['name']: record for record in available_campaigns.get('records')}
      selected_campaign = st.selectbox(
        label="Select a campaign",
        options=list(campaign_dict.keys())
      )
      selected_campaign = campaign_dict.get(selected_campaign)
      if selected_campaign:
        st.session_state.selected_campaign = selected_campaign

        if all(attr in selected_campaign for attr in ['customer_id', 'name', 'destination_url']):
          st.warning("Please make sure your CSV file contains the following columns: envelope_name, greeting_name, ma-addr_line1, ma-city, ma-state, ma-zip. Without these columns, your upload will not be processed successfully.")
          uploaded_file = st.file_uploader(
            label="Upload CSV file",
            help="Upload data for creating short URLs",
            type=["csv"]
          )
          if uploaded_file is not None:
            st.success("CSV uploaded successfully!")

            if st.session_state['trackable_urls'] is None:
              st.subheader("Response from API")
              data = {
                'customer_id': st.session_state.selected_campaign['customer_id'],
                'campaign': st.session_state.selected_campaign['name'],
                'destination_url': st.session_state.selected_campaign['destination_url'],
              }
              csv_body = send_to_api(host, uploaded_file, data)
              if csv_body:
                st.success("Data fetched from API successfully!")
                df = pd.DataFrame(csv_body)
                st.dataframe(df, hide_index=True)
                st.session_state['trackable_urls'] = df['o.rp.trackableurl'].tolist()

                qr_zip_file = tempfile.mktemp(suffix='.zip')
                generate_qr_codes(df)
                shutil.move("qrcodes.zip", qr_zip_file)

                with tempfile.NamedTemporaryFile(delete=False) as combined_zip_file:
                  with zipfile.ZipFile(combined_zip_file, 'w') as zipf:
                    zipf.writestr(
                      'processed_contacts.csv',
                      df.to_csv(index=False)
                    )
                    zipf.write(qr_zip_file, arcname='qr_codes.zip')

                file_ts = get_current_time_for_filenames()
                with open(combined_zip_file.name, 'rb') as file:
                  st.download_button(
                    label="Download CSV and QR Codes",
                    data=file,
                    file_name=f"campaign_{st.session_state.selected_campaign['name']}_bulk_upload_results_{file_ts}.zip",
                    mime="application/zip"
                  )

            else:
              csv_data = pd.DataFrame(
                {'trackableurl': st.session_state['trackable_urls']},
                index=range(len(st.session_state['trackable_urls']))).to_csv(index=False)
              generate_qr_codes(
                pd.DataFrame({'trackableurl': st.session_state['trackable_urls']})
              )
          else:
            st.warning("Please upload a CSV file")
        else:
          st.error("Selected campaign is missing required attributes")
    else:
      return st.error(available_campaigns.get('message'))

if __name__ == "__main__":
  main()
