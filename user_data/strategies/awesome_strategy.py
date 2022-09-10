import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from functools import reduce

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

class AwesomeStrategy(IStrategy):

    INTERFACE_VERSION = 3

    # Buy hyperspace params:
    buy_params = {
        'use_bull': True,
        'use_hidden_bull': True,
        "low_rsi_buy": 30,
        "high_rsi_buy": 60,
        "low_stoch_buy": 20,
        "high_stoch_buy": 80,
        "low_osc_buy": 20,
        "high_osc_buy": 80,
    }
    # Sell hyperspace params:
    sell_params = {
        'use_bear': True,
        'use_hidden_bear': True
    }    

    # Can this strategy go short?
    can_short: bool = False

    # disable minimal_roi which is >10000%
    minimal_roi = {
      "0": 100
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.08

    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = True    
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
    # Protection
    low_rsi_buy = IntParameter(0, 100, default=buy_params['low_rsi_buy'], space='buy', optimize=True)
    high_rsi_buy = IntParameter(0, 100, default=buy_params['high_rsi_buy'], space='buy', optimize=True)
    low_stoch_buy = IntParameter(0, 100, default=buy_params['low_stoch_buy'], space='buy', optimize=True)
    high_stoch_buy = IntParameter(0, 100, default=buy_params['high_stoch_buy'], space='buy', optimize=True)
    low_osc_buy = IntParameter(0, 100, default=buy_params['low_osc_buy'], space='buy', optimize=True)
    high_osc_buy = IntParameter(0, 100, default=buy_params['high_osc_buy'], space='buy', optimize=True)    

    osc = 'slowd'
    src = 'close'
    lbL = 5
    lbR = 5

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    stoch_period: int = 9

    cci_fast_period: int = 21

    cci_slow_period: int = 55

    sma1_period: int = 21
    sma2_period: int = 55
    sma3_period: int = 144

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

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
      
      #https://github.com/freqtrade/freqtrade/issues/2961
      dataframe['RSI'] = ta.RSI(dataframe[self.src], self.stoch_period)
      dataframe['RSI'] = dataframe['RSI'].fillna(0)

      #Stoch
      smoothD = 3
      SmoothK = 3
      stoch = ta.STOCH(dataframe, fastk_period=self.stoch_period, slowk_period=SmoothK,slowd_period=smoothD)
      dataframe['slowk'] = stoch['slowk']
      dataframe['slowd'] = stoch['slowd']
      dataframe['osc'] = dataframe[self.osc]

      # Fast Slow CCI
      dataframe['cci_fast'] = ta.CCI(dataframe, timeperiod=self.cci_fast_period)
      dataframe['cci_slow'] = ta.CCI(dataframe, timeperiod=self.cci_slow_period)

      dataframe['sma1'] = ta.SMA(dataframe, timeperiod=self.sma1_period)
      dataframe['sma2'] = ta.SMA(dataframe, timeperiod=self.sma2_period)
      dataframe['sma3'] = ta.SMA(dataframe, timeperiod=self.sma3_period)

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
        conditions = []

        if self.use_bull.value:
            conditions.append(
                    (
                        (dataframe['bullCond'] > 0) &
                        (dataframe['valuewhen_plFound_osc'] > self.low_osc_buy.value) &
                        (dataframe['valuewhen_plFound_osc'] < self.high_osc_buy.value) &
                        #(dataframe['EWO'] > self.ewo_high.value) &
                        (dataframe['RSI'] < self.high_rsi_buy.value) &
                        (dataframe['RSI'] > self.low_rsi_buy.value) &
                        (dataframe['slowk'] < self.high_stoch_buy.value) &
                        (dataframe['slowk'] > self.low_stoch_buy.value) &
                        (dataframe['volume'] > 0)
                    )
                )

        if self.use_hidden_bull.value:
            conditions.append(
                (
                    (dataframe['hiddenBullCond'] > 0) &
                    (dataframe['valuewhen_plFound_osc'] > self.low_osc_buy.value) &
                    (dataframe['valuewhen_plFound_osc'] < self.high_osc_buy.value) &
                    (dataframe['RSI'] < self.high_rsi_buy.value) &
                    (dataframe['RSI'] > self.low_rsi_buy.value) &
                    (dataframe['slowk'] < self.high_stoch_buy.value) &
                    (dataframe['slowk'] > self.low_stoch_buy.value) &
                    (dataframe['ADX'] > self.low_adx_buy.value) &
                    (dataframe['ADX'] < self.high_adx_buy.value) &
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
        conditions = []

        if self.use_bear.value:
            conditions.append(
                (
                    (dataframe['bearCond'] > 0) &
                    (dataframe['volume'] > 0)
                )
            )

        if self.use_hidden_bear.value:
            conditions.append(
                (
                    (dataframe['hiddenBearCond'] > 0) &
                    (dataframe['volume'] > 0)
                )
            )

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'exit_long'
            ] = 1

        dataframe.to_csv('user_data/csvs/%s_%s.csv' % (self.__class__.__name__, metadata["pair"].replace("/", "_")))

        return dataframe  


    