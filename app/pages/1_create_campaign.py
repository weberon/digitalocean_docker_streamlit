import streamlit as st
import requests

from utils import display_sidebar


def create_user_campaign(host, payload):
  url = f'https://{host}' if 'https://' not in host else host
  response = requests.post(f'{url}/campaigns', data=payload)
  if response.status_code == 201:
    return st.success(f"A campaign for {payload.get('name')} was created successfully")
  elif response.status_code == 409:
    return st.error(f"A campaign under {payload.get('name')} already exists for this user")
  else:
    st.error(response.text)


def fetch_existing_user_campaigns(host, params):
  url = f'https://{host}' if 'https://' not in host else host
  response = requests.get(f'{url}/campaigns', params=params)
  return response.json()


def main():
  secrets = st.secrets
  state = st.session_state
  host = secrets[state.group]["HOST"]
  secret_key = secrets[state.group]["SECRET_KEY"]

  st.set_page_config(page_title="Create a campaign", layout="wide")
  display_sidebar()
  st.title("Create a campaign")
  existing_campaigns = fetch_existing_user_campaigns(host, {'secret_key': secret_key})
  if existing_campaigns:
    if not existing_campaigns.get("message"):
      st.write(f"You currently have {existing_campaigns.get('count')} campaigns")
    campaigns = existing_campaigns.get('records')
    if not existing_campaigns.get("message"):
      with st.expander("Click here to view existing campaigns"):
        st.dataframe(
          data=campaigns,
          column_order=("name", "destination_url", "total", "timestamp"),
          column_config={
            'customer_id': None,
            'total': 'contacts'
          }
        )
    if existing_campaigns and existing_campaigns.get('count') == 0:
      st.info("You are yet to create any campaigns")
    else:
      name = st.text_input(
        label="Enter the name for the campaign",
        placeholder="For ex: campaignA"
      )
      destination_url = st.text_input(
        label="Enter the URL value to redirect the user to",
        placeholder="For ex: https://sample.com"
      )
      if not name:
        st.warning("The name of a campaign cannot be empty")
      if not destination_url:
        st.warning("The value for destination URL must not be empty")
      else:
        submit_btn = st.button(label="Create campaign")
        payload = {
          'secret_key': secret_key,
          'name': name,
          'destination_url': destination_url
        }

        if submit_btn:
          create_user_campaign(host=host, payload=payload)


if __name__ == '__main__':
  main()
