import streamlit as st 
from numerize.numerize import numerize as nz
# import plotly.graph_objects as go
import pandas as pd

ALLHCSVPATH = 'Data/Neighborhood_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv'

## Page Config ##
st.set_page_config(layout='wide',page_icon="🏘",initial_sidebar_state="auto")

## HELPER METHODS ##
# @st.cache(allow_output_mutation=True)
def load_data(csvpath):
    Neighborhood_Zhvi_AllHomes = pd.read_csv(csvpath,index_col=[5,7,8,6,2])
    zhvi_timeseries = Neighborhood_Zhvi_AllHomes.T
    dates = pd.to_datetime(zhvi_timeseries.index, errors='coerce').dropna()
    zhvi_timeseries = zhvi_timeseries.loc[dates.strftime("%Y-%m-%d")]
    zhvi_timeseries.index = pd.to_datetime(zhvi_timeseries.index, errors='coerce').dropna()
    return zhvi_timeseries

def data_tabs(absdf, pctdf):
    ctab, dtab = st.tabs(["💰 Absolute Value", "📈 Percent Change"])
    with ctab:
        st.subheader("Mean Price of houses in the selected states.")
        # Create a line chart with y axis as dollars
        st.line_chart(absdf)
    with dtab:
        st.subheader("Percent change in value over the time period.")
        # Create a line chart with y axis as percentage
        st.line_chart(pctdf)

def group_measure_by_location(df,measure,location,order,count):
    df_return = pd.DataFrame()
    if measure == "Mean":
        df_return = df.groupby(level=location).mean()
    if measure == "Median":
        df_return = df.groupby(level=location).median()
    if measure == "Max":
        df_return = df.groupby(level=location).max()
    if measure == "Min":
        df_return = df.groupby(level=location).min()
    if order == "Top":
        df_return = df_return.sort_values(ascending=False).head(count)
    if order == "Bottom":
        df_return = df_return.sort_values(ascending=True).head(count)
    return df_return

####################
### INTRODUCTION ###
####################
# Load Data from CSV
AllhomesTS = load_data(ALLHCSVPATH)
AllhomesTS_pct = AllhomesTS.pct_change().fillna(0)
AllStatelist = set(AllhomesTS.columns.get_level_values(0).values)
to_date = AllhomesTS.index[-1] # Last date available on the current dataset

############
# Side Bar #
############
with st.sidebar:
  # Start Header for sidebar. Here the user can select the parameters for the analysis.
  st.subheader("Please select the parameters for your analysis.")
  col1,col2,col3 = st.columns(3)
  user_inputs = {}
  user_inputs['Order'] = col1.selectbox("Top/Bottom",["Top","Bottom"])
  user_inputs['Count'] = col2.selectbox("No. of States",["5","10","15","20"])
  user_inputs['Stats'] = col3.selectbox("Stats",["Mean","Median","Max","Min"])
  FilteredStates = group_measure_by_location(AllhomesTS.iloc[-1],user_inputs['Stats'],"State",user_inputs['Order'],int(user_inputs['Count']))
  states_select = st.multiselect("Or select states for analysis:", AllStatelist, default = FilteredStates.index.values)
  
  # Select Timeframe for timeseries analysis
  st.subheader("Now, lets select the time parameters for your analysis.")
  years_timeframe_select = st.number_input("Select number of years:",min_value = 1, max_value = 20,value = 5,step = 1, format = '%g')
  from_date = to_date - pd.Timedelta(52*years_timeframe_select,"W") # Apparently there is no Years argument for time delta, so we stick with 52 weeks.
  
  # Filter by Selected States
  AbsTS_Filter = AllhomesTS[states_select].loc[from_date:to_date]
  AbsTS_Filter.columns = AbsTS_Filter.columns.remove_unused_levels()
  PctTS_Filter = AllhomesTS_pct[states_select].loc[from_date:to_date]
  PctTS_Filter.columns = PctTS_Filter.columns.remove_unused_levels()
  # If the Initial States have been selected, allow for more specific selection
  if states_select:
      iState = st.selectbox("Or focus on one State",["Select State"]+states_select)
      # If one State has been selected, allow for Metro area selection
      if iState != "Select State":
          imetro = st.selectbox("Metro",["Select Metro"]+list(set(AbsTS_Filter[iState].columns.get_level_values(0).values)))
          # If one Metro area has been selected, allow for County selection
          if imetro != "Select Metro":
              icounty = st.selectbox("County",["Select County"]+list(set(AbsTS_Filter[iState][imetro].columns.get_level_values(0).values)))
              # If one County has been selected, allow for City selection
              if icounty != "Select County":
                  icity = st.selectbox("City",["Select City"]+list(set(AbsTS_Filter[iState][imetro][icounty].columns.get_level_values(0).values)))
  
# Header Layout #
row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns((.1, 2.8, .1, 1.0, .1))
with row0_1:
    st.title("Historic Real Estate Price Analysis 🏘")
    st.markdown("This dashboard is to faciliate house prices exploration within the United States.\nThe datset is the historical ZHVI from Zillow.")
    st.markdown("If you are interested in how this app was developed check out my [Medium article](https://puente.medium.com)")
with row0_2:
    st.text("")
    st.subheader('Streamlit App by:\n [Enrique Puente](https://www.linkedin.com/in/epuente/)')

## Second Row Layout ##
row2_spacer1, row2_1, row2_spacer2 = st.columns((.1, 3.7, .1))
with row2_1:
    StatesAbsdf = AbsTS_Filter.groupby(level='State',axis=1).mean().dropna()
    StatesPctdf = PctTS_Filter.groupby(level='State',axis=1).mean().fillna(0).cumsum()
    # Data Display
    data_tabs(StatesAbsdf,StatesPctdf)

## First Row Layout ##
if states_select:
    row1_spacer1, row1_1, row1_spacer2 = st.columns((.1, 3.8, .1))
    with row1_1:
        # If nor particular State is selected, show all previously selected States 
        if iState == "Select State":
            for jState in states_select:
                with st.expander(jState):
                    metrolist = set(AbsTS_Filter[jState].columns.remove_unused_levels().levels[0].values)
                    data_tabs(AbsTS_Filter[jState].groupby(level='Metro',axis=1).mean().dropna(),PctTS_Filter[jState].groupby(level='Metro',axis=1).mean().fillna(0).cumsum())
    
## Third Row Layout ##
row3_spacer1, row3_1, row3_spacer2 = st.columns((.1, 3.7, .1))
# with row3_1:
#     for iState in states_select:
#         with st.expander(iState):
#             metrolist = set(AbsTS_Filter[iState].columns.remove_unused_levels().levels[0].values)
#             for imetro in metrolist:
#                 with st.expander(imetro):
#                     countylist = set(AbsTS_Filter[iState,imetro].columns.remove_unused_levels().levels[0].values)
#                     for icounty in countylist:
#                         with st.expander(icounty):
#                             citylist = set(AbsTS_Filter[iState,imetro,icounty].columns.remove_unused_levels().levels[0].values)
#                             for icity in citylist:
#                                 with st.expander(icity):
#                                     data_tabs(AbsTS_Filter[iState,imetro,icounty,icity],PctTS_Filter[iState,imetro,icounty,icity])
                                    