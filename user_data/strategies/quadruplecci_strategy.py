import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce
from datetime import datetime

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IStrategy, IntParameter)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

rangeUpper = 60
rangeLower = 5

def valuewhen(dataframe, condition, source, occurrence):
    copy = dataframe.copy()
    copy['colFromIndex'] = copy.index
    copy = copy.sort_values(by=[condition, 'colFromIndex'], ascending=False).reset_index(drop=True)
    copy['valuewhen'] = np.where(copy[condition] > 0, copy[source].shift(-occurrence), copy[source])
    copy['barrsince'] = copy['colFromIndex'] - copy['colFromIndex'].shift(-occurrence)
    copy.loc[
        (
            (rangeLower <= copy['barrsince']) &
            (copy['barrsince']  <= rangeUpper)
        )
    , "in_range"] = 1
    copy['in_range'] = copy['in_range'].fillna(0)
    copy = copy.sort_values(by=['colFromIndex'], ascending=True).reset_index(drop=True)
    return copy['valuewhen'], copy['in_range']

class QuadrupleCCIStrategy(IStrategy):

    INTERFACE_VERSION = 3

    # Buy hyperspace params:
    buy_params = {
        'use_bull': True,
        'use_hidden_bull': False,
    }
    # Sell hyperspace params:
    sell_params = {
        'use_bear': True,
        'use_hidden_bear': False
    }    

    # Can this strategy go short?
    can_short: bool = False

    # disable minimal_roi which is >10000%
    minimal_roi = {
      "0": 1000
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.05

    # Trailing stoploss
    trailing_stop = False
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = False    
    use_custom_stoploss = True
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured


    # Optimal timeframe for the strategy.
    timeframe = '1h'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False   

    use_bull = BooleanParameter(default=buy_params['use_bull'], space='buy', optimize=False)
    use_hidden_bull = BooleanParameter(default=buy_params['use_hidden_bull'], space='buy', optimize=False)
    use_bear = BooleanParameter(default=sell_params['use_bear'], space='sell', optimize=True)
    use_hidden_bear = BooleanParameter(default=sell_params['use_hidden_bear'], space='sell', optimize=True)


    osc = 'cci_st'
    src = 'close'
    lbL = 5
    lbR = 5

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    stoch_length: int = 9

    cci_fast_signal_length: int = 5
    cci_fast_signal_mid_band: int = 0
    cci_fast_signal_upper1_band: int = 100
    cci_fast_signal_upper2_band: int = 130
    cci_fast_signal_lower1_band: int = -100
    cci_fast_signal_lower2_band: int = -130

    cci_slow_signal_length: int = 20
    cci_slow_signal_mid_band: int = 0
    cci_slow_signal_upper1_band: int = 70
    cci_slow_signal_upper2_band: int = 100
    cci_slow_signal_lower1_band: int = -70
    cci_slow_signal_lower2_band: int = -100 
    cci_signal_lookback = 4

    cci_fast_trend_length: int = 21
    cci_slow_trend_length: int = 55   

    sma1_length: int = 21
    sma2_length: int = 55
    sma3_length: int = 144

    # Optional order type mapping.
    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'entry': 'gtc',
        'exit': 'gtc'
    }

    plot_config = {
        'main_plot': {
            'tema': {},
            'sar': {'color': 'white'},
        },
        'subplots': {
            "MACD": {
                'macd': {'color': 'blue'},
                'macdsignal': {'color': 'orange'},
            },
            "RSI": {
                'rsi': {'color': 'red'},
            }
        }
    }


    def informative_pairs(self):
      return []    

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        #print("custom_stoploss", current_profit)
        if current_profit < 0.05:
            return -1 # return a value bigger than the initial stoploss to keep using the initial stoploss

        if current_profit < 0:
            return -0.05
            
        if current_profit >= 0.10:
            return current_profit / 2
        else:
            return current_profit - 0.05 if  current_profit - 0.05 > 0 else 0
      
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
      
    #   #https://github.com/freqtrade/freqtrade/issues/2961
    #   dataframe['RSI'] = ta.RSI(dataframe[self.src], self.stoch_length)
    #   dataframe['RSI'] = dataframe['RSI'].fillna(0)

    #   #Stoch
    #   smoothD = 3
    #   SmoothK = 3
    #   stoch = ta.STOCH(dataframe, fastk_length=self.stoch_length, slowk_length=SmoothK,slowd_length=smoothD)
    #   dataframe['slowk'] = stoch['slowk']
    #   dataframe['slowd'] = stoch['slowd']
    #   dataframe['osc'] = dataframe[self.osc]

    #   dataframe['sma1'] = ta.SMA(dataframe, timeperiod=self.sma1_length)
    #   dataframe['sma2'] = ta.SMA(dataframe, timeperiod=self.sma2_length)
    #   dataframe['sma3'] = ta.SMA(dataframe, timeperiod=self.sma3_length)
      
      # Fast Slow Signal CCI - fast signal=fs, slow signal=ss
      dataframe['cci_fs'] = ta.CCI(dataframe, timeperiod=self.cci_fast_signal_length)
      dataframe['cci_ss'] = ta.CCI(dataframe, timeperiod=self.cci_slow_signal_length)
      
      # Fast Slow Trend CCI - fast trend=ft, slow trend=st
      dataframe['cci_ft'] = ta.CCI(dataframe, timeperiod=self.cci_fast_trend_length)
      dataframe['cci_st'] = ta.CCI(dataframe, timeperiod=self.cci_slow_trend_length)

      # CCI Trend Divergence - OSC 
      #dataframe = self.populate_divergence(dataframe, self.osc)

      # Retrieve best bid and best ask from the orderbook
      # ------------------------------------
      """
      # first check if dataprovider is available
      if self.dp:
          if self.dp.runmode.value in ('live', 'dry_run'):
              ob = self.dp.orderbook(metadata['pair'], 1)
              dataframe['best_bid'] = ob['bids'][0][0]
              dataframe['best_ask'] = ob['asks'][0][0]
      """
      return dataframe


    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        # buy signal 1
          1. Wait for signal CCI 20 cross above level -70
          2. signal CCI 5 must cross above level 130 within 4 bar since CCI 20 cross above level -70
        # buy signal 2
          1. if you find two CCI crosses above level 100 in the same bar, it's mean the prices will in strong upturned
        
        # notes: assume CCI 20 >= -70 and CCI 20 lookback have < -70, assume is uptrend
        """
        conditions = []
        # buy signal 1
        conditions.append(
            (
                (dataframe['cci_ss']>=self.cci_slow_signal_lower1_band) &
                #(qtpylib.crossed_above(dataframe['cci_ss'], self.cci_slow_signal_lower1_band)) &
                (qtpylib.crossed_above(dataframe['cci_fs'], self.cci_fast_signal_upper2_band)) &
                (dataframe['cci_ss'].rolling(self.cci_signal_lookback).min() < self.cci_slow_signal_lower1_band) &
                (dataframe['volume'] > 0)
            )
        )

        conditions.append(
            (
                (qtpylib.crossed_above(dataframe['cci_ss'], self.cci_slow_signal_upper2_band)) &
                (qtpylib.crossed_above(dataframe['cci_fs'], self.cci_fast_signal_upper1_band)) &
                (dataframe['volume'] > 0)
            )
        )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'enter_long'
            ] = 1        

        return dataframe    


    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        # sell signal 1
          1. Wait for signal CCI 20 cross above level -70
          2. signal CCI 5 must cross above level 130 within 4 bar since CCI 20 cross above level -70
        # sell signal 2
          1. if you find two CCI crosses below level -100 in the same bar, it;s mean the prices will in strong downtrend
        """        
        conditions = []

        conditions.append(
            (
                (dataframe['cci_ss']<=self.cci_slow_signal_upper1_band) &
                #(qtpylib.crossed_below(dataframe['cci_ss'], self.cci_slow_signal_upper1_band)) &
                (qtpylib.crossed_below(dataframe['cci_fs'], self.cci_fast_signal_lower2_band)) &
                (dataframe['cci_ss'].rolling(self.cci_signal_lookback).min() > self.cci_slow_signal_upper1_band) &
                (dataframe['volume'] > 0)
            )
        )        

        conditions.append(
            (
                (qtpylib.crossed_below(dataframe['cci_ss'], self.cci_slow_signal_lower2_band)) &
                (qtpylib.crossed_below(dataframe['cci_fs'], self.cci_fast_signal_lower1_band)) &
                (dataframe['volume'] > 0)
            )
        )        

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'exit_long'
            ] = 1
            
        return dataframe  


    def populate_divergence(self, dataframe: DataFrame, osc: str)-> DataFrame:
      dataframe['osc'] = dataframe[osc]        
      # plFound = na(pivotlow(osc, lbL, lbR)) ? false : true
      dataframe['min'] = dataframe['osc'].rolling(self.lbL).min()
      dataframe['prevMin'] = np.where(dataframe['min'] > dataframe['min'].shift(), dataframe['min'].shift(), dataframe['min'])
      dataframe.loc[
          (
              (dataframe['osc'].shift(1) == dataframe['prevMin'].shift(1)) &
              (dataframe['osc'] != dataframe['prevMin'])
          )
      , 'plFound'] = 1

      # phFound = na(pivothigh(osc, lbL, lbR)) ? false : true
      dataframe['max'] = dataframe['osc'].rolling(self.lbL).max()
      dataframe['prevMax'] = np.where(dataframe['max'] < dataframe['max'].shift(), dataframe['max'].shift(), dataframe['max'])
      dataframe.loc[
          (
            (dataframe['osc'].shift(1) == dataframe['prevMax'].shift(1)) &
            (dataframe['osc'] != dataframe['prevMax'])
          )
      , 'phFound'] = 1


      #------------------------------------------------------------------------------
      # Regular Bullish
      # Osc: Higher Low
      # oscHL = osc[lbR] > valuewhen(plFound, osc[lbR], 1) and _inRange(plFound[1])
      dataframe['valuewhen_plFound_osc'], dataframe['inrange_plFound_osc'] = valuewhen(dataframe, 'plFound', 'osc', 1)
      dataframe.loc[
          (
              (dataframe['osc'] > dataframe['valuewhen_plFound_osc']) &
              (dataframe['inrange_plFound_osc'] == 1)
              )
      , 'oscHL'] = 1

      # Price: Lower Low
      # priceLL = low[lbR] < valuewhen(plFound, low[lbR], 1)
      dataframe['valuewhen_plFound_low'], dataframe['inrange_plFound_low'] = valuewhen(dataframe, 'plFound', 'low', 1)
      dataframe.loc[
          (dataframe['low'] < dataframe['valuewhen_plFound_low'])
          , 'priceLL'] = 1
      #bullCond = plotBull and priceLL and oscHL and plFound
      dataframe.loc[
          (
              (dataframe['priceLL'] == 1) &
              (dataframe['oscHL'] == 1) &
              (dataframe['plFound'] == 1)
          )
         , 'bullCond'] = 1

      # plot(
      #      plFound ? osc[lbR] : na,
      #      offset=-lbR,
      #      title="Regular Bullish",
      #      linewidth=2,
      #      color=(bullCond ? bullColor : noneColor)
      #      )
      #
      # plotshape(
      #      bullCond ? osc[lbR] : na,
      #      offset=-lbR,
      #      title="Regular Bullish Label",
      #      text=" Bull ",
      #      style=shape.labelup,
      #      location=location.absolute,
      #      color=bullColor,
      #      textcolor=textColor
      #      )

      # //------------------------------------------------------------------------------
      # // Hidden Bullish
      # // Osc: Lower Low
      #
      # oscLL = osc[lbR] < valuewhen(plFound, osc[lbR], 1) and _inRange(plFound[1])
      dataframe['valuewhen_plFound_osc'], dataframe['inrange_plFound_osc'] = valuewhen(dataframe, 'plFound', 'osc', 1)
      dataframe.loc[
          (
              (dataframe['osc'] < dataframe['valuewhen_plFound_osc']) &
              (dataframe['inrange_plFound_osc'] == 1)
              )
      , 'oscLL'] = 1
      #
      # // Price: Higher Low
      #
      # priceHL = low[lbR] > valuewhen(plFound, low[lbR], 1)
      dataframe['valuewhen_plFound_low'], dataframe['inrange_plFound_low'] = valuewhen(dataframe,'plFound', 'low', 1)
      dataframe.loc[
          (dataframe['low'] > dataframe['valuewhen_plFound_low'])
          , 'priceHL'] = 1
      # hiddenBullCond = plotHiddenBull and priceHL and oscLL and plFound
      dataframe.loc[
          (
              (dataframe['priceHL'] == 1) &
              (dataframe['oscLL'] == 1) &
              (dataframe['plFound'] == 1)
          )
          , 'hiddenBullCond'] = 1
        #
        # plot(
        #      plFound ? osc[lbR] : na,
        #      offset=-lbR,
        #      title="Hidden Bullish",
        #      linewidth=2,
        #      color=(hiddenBullCond ? hiddenBullColor : noneColor)
        #      )
        #
        # plotshape(
        #      hiddenBullCond ? osc[lbR] : na,
        #      offset=-lbR,
        #      title="Hidden Bullish Label",
        #      text=" H Bull ",
        #      style=shape.labelup,
        #      location=location.absolute,
        #      color=bullColor,
        #      textcolor=textColor
        #      )
        #
        # //------------------------------------------------------------------------------
        # // Regular Bearish
        # // Osc: Lower High
        #
        # oscLH = osc[lbR] < valuewhen(phFound, osc[lbR], 1) and _inRange(phFound[1])
      dataframe['valuewhen_phFound_osc'], dataframe['inrange_phFound_osc'] = valuewhen(dataframe, 'phFound', 'osc', 1)
      dataframe.loc[
          (
              (dataframe['osc'] < dataframe['valuewhen_phFound_osc']) &
              (dataframe['inrange_phFound_osc'] == 1)
              )
      , 'oscLH'] = 1
      #
      # // Price: Higher High
      #
      # priceHH = high[lbR] > valuewhen(phFound, high[lbR], 1)
      dataframe['valuewhen_phFound_high'], dataframe['inrange_phFound_high'] = valuewhen(dataframe, 'phFound', 'high', 1)
      dataframe.loc[
          (dataframe['high'] > dataframe['valuewhen_phFound_high'])
          , 'priceHH'] = 1
      #
      # bearCond = plotBear and priceHH and oscLH and phFound
      dataframe.loc[
          (
              (dataframe['priceHH'] == 1) &
              (dataframe['oscLH'] == 1) &
              (dataframe['phFound'] == 1)
          )
          , 'bearCond'] = 1
        #
        # plot(
        #      phFound ? osc[lbR] : na,
        #      offset=-lbR,
        #      title="Regular Bearish",
        #      linewidth=2,
        #      color=(bearCond ? bearColor : noneColor)
        #      )
        #
        # plotshape(
        #      bearCond ? osc[lbR] : na,
        #      offset=-lbR,
        #      title="Regular Bearish Label",
        #      text=" Bear ",
        #      style=shape.labeldown,
        #      location=location.absolute,
        #      color=bearColor,
        #      textcolor=textColor
        #      )
        #
        # //------------------------------------------------------------------------------
        # // Hidden Bearish
        # // Osc: Higher High
        #
        # oscHH = osc[lbR] > valuewhen(phFound, osc[lbR], 1) and _inRange(phFound[1])
      dataframe['valuewhen_phFound_osc'], dataframe['inrange_phFound_osc'] = valuewhen(dataframe, 'phFound', 'osc', 1)
      dataframe.loc[
          (
              (dataframe['osc'] > dataframe['valuewhen_phFound_osc']) &
              (dataframe['inrange_phFound_osc'] == 1)
              )
      , 'oscHH'] = 1
      #
      # // Price: Lower High
      #
      # priceLH = high[lbR] < valuewhen(phFound, high[lbR], 1)
      dataframe['valuewhen_phFound_high'], dataframe['inrange_phFound_high'] = valuewhen(dataframe, 'phFound', 'high', 1)
      dataframe.loc[
          (dataframe['high'] < dataframe['valuewhen_phFound_high'])
          , 'priceLH'] = 1
      #
      # hiddenBearCond = plotHiddenBear and priceLH and oscHH and phFound
      dataframe.loc[
          (
              (dataframe['priceLH'] == 1) &
              (dataframe['oscHH'] == 1) &
              (dataframe['phFound'] == 1)
         )
         , 'hiddenBearCond'] = 1
      return dataframe


    