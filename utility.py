import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np


def data_prep(dataframe):  # for OO live trade log
    # convert to datatime & removed hour and time
    dataframe["Date Opened"] = pd.to_datetime(dataframe["Date Opened"]).dt.date
    dataframe["Date Closed"] = pd.to_datetime(dataframe["Date Closed"]).dt.date
    # make sure it's in ascending order
    dataframe = dataframe.sort_values(by="Date Opened", ascending=True).reset_index()


def get_simple_stat(dataframe):  # return entry number, data range,
    trade_number = len(dataframe.index)
    start_date = dataframe["Date Opened"].min()
    end_date = dataframe["Date Opened"].max()
    strategy_number = len(dataframe["Strategy"].unique())
    strategy_list = dataframe["Strategy"].unique()
    return trade_number, start_date, end_date, strategy_number, strategy_list


def show_simple_stat(dataframe):  # display stats in
    trade_number, start_date, end_date, strategy_number, strategy_list = get_simple_stat(dataframe)

    st.subheader("Quick Stats", anchor=False)
    col1, col2, col3, col4 = st.columns(4, border=True)
    col1.metric(
        label="Trade Number",
        value=f"{trade_number}",
    )
    col2.metric(
        label="Strategy Number",
        value=f"{strategy_number}",
    )
    col3.metric(
        label="Start Date",
        value=f"{start_date}",
    )
    col4.metric(
        label="End Date",
        value=f"{end_date}",
    )
    # print out trantegy list with popover
    popover_strategy = st.popover("show stratgey names")
    markdown_list = ""
    for item in strategy_list:
        markdown_list += f"* {item}\n"
    popover_strategy.caption(markdown_list)  # or use markdown


def trade_filter_form(dataframe, id):  # create filter form inside a popover, and return filtered data
    # header at left column
    st.text("Selected filters")
    popover_filter = st.popover("Filters")
    with popover_filter.form(key=f"filter_form_{id}"):
        # select envelopes
        selected_strat_list = st.pills(
            "Select one or multiple envelopes",
            dataframe["Strategy"].unique(),
            selection_mode="multi",
            default=dataframe["Strategy"].unique(),  # default to select all strategies
        )
        # select dates
        min_date_val = dataframe["Date Opened"].min()  #### somehow .date() used in data prep. necessary for slides.
        max_date_val = dataframe["Date Opened"].max()

        selected_date = st.slider(
            f"Select a range of dates (available dates from **{min_date_val:%Y/%m/%d}** to **{max_date_val:%Y/%m/%d}**)",
            min_value=min_date_val,
            max_value=max_date_val,
            value=(min_date_val, max_date_val),
            format="YYYY-MM-DD",
            key=f"filter_slider_{id}",
        )

        # submit_button
        st.caption("Click button below to apply the filters above.")
        submit_button = st.form_submit_button("Apply Filters", key=f"filter_button_{id}")
        if submit_button:
            if not selected_strat_list:
                st.error("Please select at least one strategy above.")
                st.stop()

    # confirm selected filter  (outside of the form)
    # min_date_val = selected_date[0]
    # max_date_val = selected_date[1]
    popover_filter.caption(f"Selected Date: \n * From **{selected_date[0]}** to **{selected_date[1]}**")
    markdown_strat_list = "Selected Strategies: \n"
    for item in selected_strat_list:
        markdown_strat_list += f" * {item}\n"
    popover_filter.caption(markdown_strat_list)  # or use markdown

    # create filtered data (outside of the form)
    df_filtered = dataframe[
        (dataframe["Date Opened"] >= selected_date[0])
        & (dataframe["Date Opened"] <= selected_date[1])
        & dataframe["Strategy"].isin(selected_strat_list)
    ]
    return df_filtered


# convert to PL type dataframe + input: starting fund. Return df_PL, starting_fund
def convert_to_PL(dataframe, starting_fund=50000, id="input_fund"):
    starting_fund = st.number_input("Starting Fund: ", min_value=10, value=50000, key=f"starting_fund_input_{id}")
    st.caption("_* required to calculate drawdown and CAGR_")
    # ==== P/L curve vs Date Closed, and DD =====
    df_PL = dataframe.groupby("Date Closed")["P/L"].agg(["sum", "count"]).reset_index()
    df_PL["cum_PL"] = df_PL["sum"].cumsum()  # cumulative PL. 'sum' column is daily PL.
    df_PL["Fund"] = df_PL["cum_PL"] + starting_fund
    df_PL["DD"] = df_PL["cum_PL"].cummax() - df_PL["cum_PL"]  # DD in amount
    # DD based on starting fund to remove sequence return risk
    df_PL["DD_pct_startingfund"] = df_PL["DD"] / starting_fund * 100
    # ==== DD duration (in trading days) =====
    df_PL["DD_duration"] = None  # create a new column
    for t in range(len(df_PL)):
        if df_PL["DD"].iloc[t] == 0:
            df_PL["DD_duration"].iat[t] = 0
        else:
            df_PL["DD_duration"].iat[t] = df_PL["DD_duration"].iat[t - 1] + (
                df_PL["Date Closed"][t] - df_PL["Date Closed"][t - 1]
            ) // np.timedelta64(1, "D")
            # calculate calenda days
    df_PL.rename(columns={"sum": "Daily_PL", "count": "Daily_count"}, inplace=True)
    return df_PL, starting_fund


# convert to PL type dataframe + input: starting fund. Return df_PL, starting_fund
def convert_to_PL_no_starting_fund(dataframe):
    # ==== P/L curve vs Date Closed, and DD =====
    df_PL = dataframe.groupby("Date Closed")["P/L"].agg(["sum", "count"]).reset_index()
    df_PL["cum_PL"] = df_PL["sum"].cumsum()  # cumulative PL. 'sum' column is daily PL.
    # ---- no starting fund, no Fund column -----
    # df_PL["Fund"] = df_PL["cum_PL"] + starting_fund
    df_PL["DD"] = df_PL["cum_PL"].cummax() - df_PL["cum_PL"]  # DD in amount
    # # ---- no starting fund, no DD pct -----
    # df_PL["DD_pct_startingfund"] = df_PL["DD"] / starting_fund * 100
    # ==== DD duration (in trading days) =====
    df_PL["DD_duration"] = None  # create a new column
    for t in range(len(df_PL)):
        if df_PL["DD"].iloc[t] == 0:
            df_PL["DD_duration"].iat[t] = 0
        else:
            df_PL["DD_duration"].iat[t] = df_PL["DD_duration"].iat[t - 1] + (
                df_PL["Date Closed"][t] - df_PL["Date Closed"][t - 1]
            ) // np.timedelta64(1, "D")
            # calculate calenda days
    df_PL.rename(columns={"sum": "Daily_PL", "count": "Daily_count"}, inplace=True)
    return df_PL


def show_daily_PL_cum_PL_curve(dataframe):  # need to use PL type dataframe
    fig = make_subplots(
        rows=2,
        cols=1,
        row_heights=[0.3, 0.25],
        shared_xaxes=True,
        vertical_spacing=0.05,
    )
    ######  PL curve  ######
    fig.add_trace(
        go.Scatter(
            x=dataframe["Date Closed"],
            y=dataframe["cum_PL"],
            name="Cumulative P/L",
            line_color="#e1aa00",
            mode="lines+markers",
            marker=dict(
                symbol="circle",
                size=4,
                color="#e1aa00",  # opacity=1,
                line=dict(
                    # color="#1A1A1A",  # Set the outline color
                    width=0.2,
                ),
            ),
        ),
        row=1,
        col=1,
    )

    ######  Daily PL bar chart ######
    bar_colors = ["#f99898" if v < 0 else "#5eb6af" for v in dataframe["Daily_PL"]]  # Create a color list

    fig.add_trace(
        go.Bar(
            x=dataframe["Date Closed"],
            y=dataframe["Daily_PL"],
            name="Daily P/L",
            opacity=0.8,
            marker_color=bar_colors,
        ),
        row=2,
        col=1,
    )

    fig.update_yaxes(
        title_text="Cumulative P/L",
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="Daily P/L",
        row=2,
        col=1,
    )

    fig.update_layout(
        height=500,
        width=800,
        title_text="Daily and Cumulative P/L",
        # xaxis_title="Date",
        template="plotly_dark",
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=1.05,
            xanchor="center",
            x=0.5,
        ),
    )
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=False)


def show_PL_DD_plot(dataframe, starting_fund):  # need to use PL type dataframe. Starting fund used for PL %
    fig = make_subplots(
        rows=3,
        cols=1,
        row_heights=[0.15, 0.15, 0.15],
        shared_xaxes=True,
        vertical_spacing=0.06,
    )
    ######  Live PL % ######
    fig.add_trace(
        go.Scatter(
            x=dataframe["Date Closed"],
            y=dataframe["cum_PL"] / starting_fund * 100,
            name="PL %",
            line_color="#e1aa00",
            mode="lines+markers",
            marker=dict(
                symbol="circle",
                size=4,
                color="#e1aa00",  # opacity=1,
                line=dict(
                    # color="#1A1A1A",  # Set the outline color
                    width=0.2,
                ),
            ),
        ),
        row=1,
        col=1,
    )
    ######  DD % based on starting fund ######
    fig.add_trace(
        go.Scatter(
            x=dataframe["Date Closed"],
            y=dataframe["DD_pct_startingfund"],
            name="DD / starting fund",
            fill="tozeroy",
            fillcolor="rgba(255, 0, 0, 0.15)",  # Red fill. last value is opacity
            line_color="red",
        ),
        row=2,
        col=1,
    )
    ######  DD duration ######
    fig.add_trace(
        go.Scatter(
            x=dataframe["Date Closed"],
            y=dataframe["DD_duration"],
            name="DD Duration (days)",
            fill="tozeroy",
            fillcolor="rgba(0, 176, 160, 0.15)",  # last value is opacity
            line_color="#00b0a0",  # same green used on OO website
        ),
        row=3,
        col=1,
    )
    # ######  DD amount ######
    # fig.add_trace(
    #     go.Scatter(
    #         x=dataframe["Date Closed"],
    #         y=dataframe["DD"],
    #         name="DD amount",
    #     ),
    #     row=4,
    #     col=1,
    # )

    fig.update_yaxes(title_text="P/L %", row=1, col=1)
    fig.update_yaxes(title_text="DD %", row=2, col=1)
    fig.update_yaxes(title_text="DD days", row=3, col=1)
    # fig.update_yaxes(title_text="DD $", row=4, col=1)

    # fig.update_xaxes(showline=True, linecolor="#525252", linewidth=0.5, mirror=True)
    # fig.update_yaxes(showline=True, linecolor="#525252", linewidth=0.5, mirror=True)

    fig.update_layout(
        height=500,
        width=500,
        title_text="P/L & Draw Down Graphs",
        # xaxis_title="Date",
        template="plotly_dark",
        legend=dict(
            orientation="h",
            yanchor="middle",
            y=1.08,
            xanchor="center",
            x=0.5,
        ),
    )
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=False)
        # some notes (inside the container)
        st.caption(
            "_Note: The Drawdown is calculated based starting fund instead of recent PL max._", text_alignment="center"
        )


def show_PL_per_strategy_bar_chart(dataframe):
    pivot_table = (
        pd.pivot_table(dataframe, values="P/L", index="Strategy", aggfunc="sum").reset_index().sort_values(by="P/L")
    )
    fig = go.Figure()
    ## bar chart: PL per strategy ##
    fig.add_trace(
        go.Bar(
            y=pivot_table["Strategy"],
            x=pivot_table["P/L"],
            # x=pivot_table["P/L"] / starting_fund * 100, # convert to percentage of starting fund
            orientation="h",
            # name='xxx',
            # opacity=1,
        )
    )
    fig.update_layout(
        title="PL per Strategy",
        # yaxis_title='Strategy',
        # xaxis_title="PL per Strategy",
        width=800,
        height=170 + 25 * len(pivot_table),  # adjust height based on # of strategies
        template="plotly_dark",
        # legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
    )
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=False)


def show_open_date_per_strategy(dataframe):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=dataframe["Date Opened"],
            y=dataframe["Strategy"],
            mode="markers",
            # name="",
            marker=dict(
                color="#776538",
                size=8,
                symbol="circle",
                line=dict(
                    width=1.5,
                    color="#e1aa00",
                ),
            ),
        )
    )

    fig.update_layout(
        title="Trade open date per strategy",
        xaxis_title="Date Opened",
        # yaxis_title="",
        width=800,
        height=170 + 25 * len(dataframe["Strategy"].unique()),  # adjusted by strategy number
        template="plotly_dark",
        # legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
    )
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=False)


def show_daily_PL_distribution_daily_trades(dataframe, starting_fund):  # need to use PL type dataframe
    bar_color = "#636efa"
    # --- daily PL distribution ---
    fig_dailyPL = px.histogram(
        dataframe,
        x=dataframe["Daily_PL"] / starting_fund * 100,  # PL as a percentage of starting fund
        nbins=80,
        title="Daily PL Distribution",
        color_discrete_sequence=[bar_color] * len(dataframe),  # use single color for all bars
        opacity=0.8,
    )
    fig_dailyPL.update_layout(
        width=500,
        height=360,
        xaxis_title_text="Daily PL (% of starting fund)",
        yaxis_title_text="Count",
        bargap=0.1,  # gap between bars of adjacent location coordinates
        template="plotly_dark",
        # xaxis=dict(
        #     tickmode="linear",
        #     tick0=0,
        #     # dtick = 200
        # ),
    )
    # --- daily trade number distribution ---
    fig_dailytrades = px.histogram(
        dataframe,
        x="Daily_count",
        nbins=20,
        title="Daily Trade # Distribution",
        color_discrete_sequence=[bar_color] * len(dataframe),  # use single color for all bars
        opacity=0.8,
    )

    fig_dailytrades.update_layout(
        width=500,
        height=360,
        xaxis_title_text="Daily (Closed) Trade Number",
        yaxis_title_text="Count",
        bargap=0.1,  # gap between bars of adjacent location coordinates
        template="plotly_dark",
        # xaxis = dict(
        #     tickmode = 'linear',
        #     tick0 = 0,
        #     dtick = 100
        # )
    )
    with st.container(border=True):
        col1, col2 = st.columns(2)
        col1.plotly_chart(fig_dailyPL, use_container_width=False)
        col2.plotly_chart(fig_dailytrades, use_container_width=False)
