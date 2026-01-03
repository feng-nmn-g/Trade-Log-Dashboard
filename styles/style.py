import streamlit as st


def style_tidy_up():
    st.markdown(
        """
    <style>
           /* Remove top header and main menu?? */
           MainMenu {visibility: hidden;}
           header {visibility: hidden;}
           
           /* ----- Metric value size ----- */
           [data-testid="stMetricValue"] {
        #    font-size: 30px; /* use px or % */
           font-size: 150%;
           }

           /* ----- Metric label size ----- */
           [data-testid="stMetricLabel"] {
        #    font-size: 30px; /* use px or % */
           font-size: 40%;
           }


           /* Remove blank space at top and bottom */ 
           .block-container {
               padding-top: 1rem;
               padding-bottom: 3rem;
            }
           
           /* Remove blank space at the center canvas */ 
           .st-emotion-cache-z5fcl4 {
               position: relative;
               top: -62px;
               }
           
           /* Make the toolbar transparent and the content below it clickable */ 
           .st-emotion-cache-18ni7ap {
               pointer-events: none;
               background: rgb(255 255 255 / 0%)
               }
           .st-emotion-cache-zq5wmm {
               pointer-events: auto;
               background: rgb(255 255 255);
               border-radius: 5px;
               }
    </style>
    """,
        unsafe_allow_html=True,
    )
