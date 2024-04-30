import requests
import json

import streamlit as st
from utils import display_sidebar


# Collect user email and signup to the application
def user_signup(endpoint: str, email: str) -> dict:
  url = f'https://{endpoint}' if 'https://' not in endpoint else endpoint
  response = requests.post(f'{url}/users', json={'email': email})
  if response.ok:
    return response.json()
  else:
    body = response.json()
    message = body.get('message')
    error = f"Something went wrong while attempting to register: {message}"
    return st.error(error)


# Display the credentials on to the app
def display_user_details(data: dict) -> any:
  """Function that will display the result of the user signup on the screen"""
  if data:
      message = data.get('message')
      st.success(message)
      details = data.get('details')

      # Store details from response to session state
      if 'secret_key' not in st.session_state:
        st.session_state['secret_key'] = details.get('app_secret')
      if 'pixel_id' not in st.session_state:
        st.session_state['pixel_id'] = details.get('pixel_id')

      body = {
        'customer_id': details.get('cid'),
        'secret_key': details.get('app_secret'),
        'pixel_id': details.get('pixel_id'),
        'email_address': details.get('email'),
      }
      st.json(body=body, expanded=True)
      st.download_button(
        label="Download credentials",
        data=json.dumps(body),
        file_name=f'credentials_user_{details.get("cid")}.json',
        mime='application/json'
      )
  else:
    st.error("No response was received from the application.")


def main():
  secrets = st.secrets
  params = st.query_params.to_dict()

  if not params:
    return st.error("This app needs query parameters to proceed")
  else:
    group = params.get("s", None)
    host = secrets[group]["HOST"]
    st.set_page_config(page_title="User registration", layout="wide")
    display_sidebar()
    st.title("User registration")
    email = st.text_input(
      label='Your email address',
      help='Enter the value for the email address you wish to register with',
      placeholder='For ex: name@example.com'
    )
    submit_btn = st.button(label='Register')

    if submit_btn:
      if not email:
        st.warning("E-mail address cannot be left empty")
      else:
        try:
          data = user_signup(endpoint=host.lower(), email=email.lower())
          display_user_details(data)
        except (ConnectionError, Exception) as e:
          st.error(str(e))


if __name__ == '__main__':
  main()
