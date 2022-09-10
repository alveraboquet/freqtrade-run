

## Command


# Download data
```
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --days 10 -t 1h
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 12h
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 1d
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 8h
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 2h
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 1h
docker-compose run --rm freqtrade download-data --pairs BTC/USDT --exchange binance --timerange 20170817-20220909 -t 1w
docker-compose run --rm freqtrade download-data --pairs ETH/USDT --exchange binance --timerange 20170817-20220909 -t 4h
docker-compose run --rm freqtrade download-data --pairs DOGE/USDT --exchange binance --timerange 20170817-20220909 -t 8h
docker-compose run --rm freqtrade download-data --pairs ETH/USDT --exchange binance --timerange 20170817-20220909 -t 1h
```


# Back Testing
```
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy AwesomeStrategy --timerange 20220823-20220902 -i 1h

docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 12h
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 8h
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 1d
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 4h
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 2h
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 1h
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 1w

docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 1h --pairs ETH/USDT
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20190101-20220909 -i 1h --pairs ETH/USDT
docker-compose run --rm freqtrade backtesting --config user_data/config.json --strategy QuadrupleCCIStrategy --timerange 20170817-20220909 -i 8h --pairs DOGE/USDT
```

# Plot - required freqtradeorg/freqtrade:2022.8_plot

```
docker-compose run --rm freqtrade plot-dataframe --strategy AwesomeStrategy -p BTC/USDT --timerange=20220823-20220905 --no-trades --indicators2 'stoch_k' 'stoch_d'
docker-compose run --rm freqtrade plot-dataframe --strategy AwesomeStrategy -p BTC/USDT --timerange=20220823-20220905 --no-trades --indicators2 'cci_fast' 'cci_slow'

docker-compose run --rm freqtrade plot-dataframe --strategy QuadrupleCCIStrategy -p BTC/USDT --timerange=20170817-20220909 --indicators2 'cci_fs' 'cci_ss' -i 12h
```


# Jupyter Notebook
```
docker-compose -f docker/docker-compose-jupyter.yml up
```


# Custom stopless 

https://www.freqtrade.io/en/stable/strategy-callbacks/