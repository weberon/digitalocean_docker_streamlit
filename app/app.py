import streamlit as st

from utils import display_sidebar

secrets = st.secrets
state = st.session_state
params = st.query_params.to_dict()

if "group" not in state:
  state.group = None

group = params.get("s", None)

if group in secrets:
  state.group = group


def main():
  st.set_page_config(page_title="User registration", layout="wide")
  display_sidebar()
  st.title("Trackable QRcodes")

  st.markdown('''
    #### Generate trackable QRcodes for print mailers

    - Sign-up for your account and save your credentials
    - Create a campaign by Uploading contacts
    - View Campaigns
  ''')


if __name__ == '__main__':
  main()
