import streamlit as st
import pandas as pd
from utility import *  # import funtions
from styles.style import *

# ---- style, page set up, etc ----
style_tidy_up()
st.set_page_config(
    page_title="Trade Log Tracker",
    page_icon=":material/analytics:",
    # layout="wide",
    # initial_sidebar_state="expanded",
)

# ---- session state initialize ----
if "store_radio_index" not in st.session_state:
    st.session_state.store_radio_index = 0  # this is the default radio index

# ---- page content starts here ----
st.header("Trade Log Tracker & Analysis", anchor=False)

tab_label = [
    ":material/upload: Import Data",
    ":material/team_dashboard: Summary",
    ":material/bar_chart_4_bars: Portfolio",
    ":material/bar_chart_4_bars: Strategies",
]
tab_import, tab_summary, tab_port, tab_per_strat = st.tabs(tabs=tab_label)

with tab_import:
    # --- data selection: use demo data or import data ---
    radio_labels = ["Import Data", "Use Demo Data"]
    radio_captions = ["Import your spending data below (i.e. option omega trade log)", "Use built in demo data."]

    st.subheader("Use demo data or import data", anchor=False)
    select_data_source = st.radio(
        "Upload your data or select demo data",
        options=range(len(radio_labels)),  # use index numbers for radio output
        format_func=radio_labels.__getitem__,  # Use labels for display
        captions=radio_captions,
        key="key_radio_index",
        index=st.session_state.store_radio_index,
    )
    # store selected key_radio_index to store_radio_index
    st.session_state.store_radio_index = st.session_state.key_radio_index

    _, col_file_uploader, _ = st.columns((0.15, 1, 0.15))
    # --- file uploader widget (middle column) ---
    file_uploader_disabled = [False, True]  # radio index 0: disabled=False, 1: disabled=True
    uploaded_file = col_file_uploader.file_uploader(
        "Upload csv data (Select 'Import Data' to enable the uploader. Once a new file is uploaded, it will overwrite existing data)",
        type="csv",
        disabled=file_uploader_disabled[st.session_state.store_radio_index],
    )

    # --- Get df data and call out data_prep() ---
    if st.session_state.store_radio_index == 0:  # Upload Data option
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            data_prep(df)
            st.session_state["df"] = df
    if st.session_state.store_radio_index == 1:  # Use Demo Data option
        df = pd.read_csv("data/Demo_trade_log.csv")
        data_prep(df)
        st.session_state["df"] = df

    # --- check st.session_state["df"] ---
    if "df" in st.session_state:
        st.markdown("---")
        df = st.session_state["df"]
        st.markdown(f"> Data available. Entries:  __{df["Date Opened"].count()}__")
        with st.expander("A quick preview of loaded data (a few top entries)"):
            st.dataframe(df.head(), hide_index=True)  # type: ignore
    else:
        col_file_uploader.warning(
            "Data not imported yet: please import data or select the demo data from 'Import Data' tab."
        )

with tab_summary:
    if "df" not in st.session_state:
        st.warning("Data not imported yet: please import data or select the demo data from 'Import Data' tab.")
    else:
        show_simple_stat(st.session_state.df)
        df_PL_summary = convert_to_PL_no_starting_fund(st.session_state.df)
        show_daily_PL_cum_PL_curve(df_PL_summary)

with tab_port:
    if "df" not in st.session_state:
        st.warning("Data not imported yet: please import data or select the demo data from 'Import Data' tab.")
    else:
        col1, col2 = st.columns((1, 4), vertical_alignment="top")
        with col1:
            df_filtered = trade_filter_form(st.session_state.df, id="port")  # display and apply filters
            # st.space("small")
            df_PL, starting_fund = convert_to_PL(df_filtered, id="port_fund")  # need strating fund input
        with col2:
            show_PL_DD_plot(df_PL, starting_fund)

with tab_per_strat:
    if "df" not in st.session_state:
        st.warning("Data not imported yet: please import data or select the demo data from 'Import Data' tab.")
    else:
        col1, col2 = st.columns((1, 4), vertical_alignment="top")
        with col1:
            df_filtered = trade_filter_form(st.session_state.df, id="strat")  # display and apply filters
            # st.space("small")
            df_PL, starting_fund = convert_to_PL(df_filtered, id="strat_fund")  # need strating fund input
        with col2:
            show_PL_per_strategy_bar_chart(df_filtered)
            show_open_date_per_strategy(df_filtered)
            show_daily_PL_distribution_daily_trades(df_PL, starting_fund)
