import streamlit as st
import os


def display_sidebar():

  with st.sidebar:
    asset_path = "assets/rp-logo.png"
    st.image(f'{asset_path}', use_column_width=True)

    st.divider()

    # Use shortcodes for labels from here https://streamlit-emoji-shortcodes-streamlit-app-gwckff.streamlit.app/
    st.page_link(
      "app.py",
      label=":house:   Home",
      use_container_width=True
    )

    # st.page_link(
    #   "pages/1_create_user.py",
    #   label="Sign-up",
    #   use_container_width=True
    # )
    st.page_link(
      "pages/1_create_campaign.py",
      label="Create Campaign",
      use_container_width=True
    )
    st.page_link(
      "pages/2_upload_records_in_bulk.py",
      label="Upload contacts against campaign",
      use_container_width=True
    )
    st.page_link(
      "pages/4_see_statistics_for_short_url.py",
      label="View campaign statistics",
      use_container_width=True
    )
    # st.page_link(
    #   "pages/5_see_tracking_pixel_records.py",
    #   label="View Activity",
    #   use_container_width=True,
    # )
