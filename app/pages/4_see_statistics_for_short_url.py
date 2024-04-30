import json
import pandas as pd
import numpy as np
import requests
import streamlit as st

from pandas import json_normalize
from pprint import pprint,pformat
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, ColumnsAutoSizeMode
from utils import display_sidebar

st.set_page_config(
    page_title="Dashboard",
    page_icon="",
    layout="wide",
    menu_items={
        'Get Help': 'https://www.reachpersona.com/',
        'Report a bug': "https://www.reachpersona.com/",
        'About': "#*Dashboard*"
    }
)
display_sidebar()

hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        header[data-testid="stHeader"] {visibility: hidden;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

secrets = st.secrets
state = st.session_state
host = secrets[state.group]["HOST"]
secret_key = secrets[state.group]["SECRET_KEY"]

if "group" in st.session_state and state.group == st.session_state["group"]:
  pass
else:
  st.cache_data.clear()
  if state.group in st.secrets:
    st.session_state["group"] = state.group
  else:
    st.session_state["group"] = None
    st.stop()

API = secrets[state.group]["API"]
USER = secrets[state.group]["USER"]
PASS = secrets[state.group]["PASS"]
SECRET_KEY = secrets[state.group]["SECRET_KEY"]
ENDPOINT = secrets[state.group]["HOST"]


def format_prepped_request(prepped, encoding=None):
    # prepped has .method, .path_url, .headers and .body attribute to view the request
    encoding = encoding or requests.utils.get_encoding_from_headers(prepped.headers)
    # body = prepped.body.decode(encoding) if encoding else '<binary data>'
    body = ''
    headers = '\n'.join(['{}: {}'.format(*hv) for hv in prepped.headers.items()])
    return f'''{prepped.method} {prepped.path_url} HTTP/1.1
    {headers}

    {body}'''


def get_response(endpoint):
  endpoint = f'{API}/api/{endpoint}'
  session = requests.Session()
  request = requests.Request('GET', endpoint, auth=(USER, PASS))
  prepped = session.prepare_request(request)

  print("Sending request:")
  print(format_prepped_request(prepped, 'utf8'))
  print()
  response = session.send(prepped, verify=True)
  return response


@st.cache_data()
def get_contact_activity(contact_id):
    response = requests.get(f"https://{ENDPOINT}/related", params={'secret_key': SECRET_KEY, 'path': contact_id})
    body = response.json()
    return json_normalize(body['records'])


@st.cache_data()
def get_contact(contact_id):
    data = json.loads(get_response(f"contacts/{contact_id}").text)
    return json_normalize(data["contact"]["fields"]["all"])


@st.cache_data()
def get_contacts(campaign_name):
    response = requests.get(f"https://{ENDPOINT}/records", params={'secret_key': SECRET_KEY, 'campaign': campaign_name})
    return json_normalize(response.json())


def get_campaigns(search=None):
    response = requests.get(f"https://{ENDPOINT}/campaigns", params={'secret_key': SECRET_KEY})
    body = response.json()
    return body['records']


def df_cols(df):
    return df.columns.values.tolist()


def make_ag(df1):
    gb = GridOptionsBuilder.from_dataframe(df1)
    gb.configure_selection("single")
    gb.configure_grid_options(domLayout='normal')
    go = gb.build()
    return AgGrid(
        df1,
        gridOptions=go,
        width="100%",
        enable_enterprise_modules=False,
        fit_columns_on_grid_load=True,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
    )


st.header("Campaigns")
df0_ = pd.DataFrame(get_campaigns(""))
df0_cols = df_cols(df0_)
df0 = df0_[[
            "name", "destination_url", "timestamp"
          ]].rename(columns={
            "name": "campaign"
          })
col1, col2 = st.columns(2)
with st.container():
    with col1:
        grid_response = make_ag(df0)

with st.spinner("Displaying results..."):
    selected = grid_response['selected_rows']
    if selected:
        selected_df = pd.DataFrame(selected).apply(pd.to_numeric, errors='coerce')
        campaign_name = selected[0]["campaign"]
        with col2:
            # with st.expander("Selected Campaign", expanded=False):
                q0 = df0[df0_["name"] == campaign_name].iloc[0].rename("").to_frame()
                # q0[" "] = " " #hack to make last column resizable
                st.dataframe(q0, use_container_width=True)
        st.subheader("Responded Contacts")
        col_l, col_r = st.columns(2)
        qdf_ = pd.DataFrame(get_contacts(campaign_name))
        if not qdf_.empty:
            qdf_cols = df_cols(qdf_)
            qdf_disp = qdf_
            qdf = qdf_[[
                    "id",
                    "data_row.Property Street",
                    "data_row.Property Zip",
                    "data_row.Owner First Name",
                    "data_row.Owner Last Name",
                    "timestamp",
                ]].rename(columns={
                    "id": "qrcode",
                    "data_row.Property Street": "Street",
                    "data_row.Property Zip": "Zipcode",
                    "data_row.Owner First Name": "First Name",
                    "data_row.Owner Last Name": "Last Name",
                })
            with col_l:
                gr_resp1 = make_ag(qdf)
            sel1 = gr_resp1['selected_rows']
            if sel1:
                sel1_df = pd.DataFrame(sel1).apply(pd.to_numeric, errors='coerce')
                c_id = sel1[0]["qrcode"]
                with col_r:
                    # with st.expander("Selected Contact", expanded=True):
                        q1 = qdf_disp.loc[qdf_disp["id"] == c_id].iloc[0].rename("").to_frame()
                        # q1[" "] = " " #hack to make last column resizable
                        st.dataframe(q1, use_container_width=True)
                st.subheader("Contact Visits")
                col_a, col_b = st.columns(2)
                cdf_ = pd.DataFrame(get_contact_activity(c_id))
                if not cdf_.empty:
                    cdf_cols = df_cols(cdf_)
                    # with st.expander("Available Fields"):
                    #    st.write(cdf_cols)
                    cdf = cdf_[["timestamp",
                            "path"
                        ]].rename(columns={
                            "path": "qrcode"
                        })
                    cdf_d = cdf_
                    with col_a:
                        gr_resp2 = make_ag(cdf)
                    sel2 = gr_resp2['selected_rows']
                    if sel2:
                        with col_b:
                            q2 = cdf_d.iloc[int(sel2[0]["_selectedRowNodeInfo"]["nodeId"])].rename("").to_frame()
                            # q2[" "] = " " #hack to make last column resizable
                            st.dataframe(q2, use_container_width=True)