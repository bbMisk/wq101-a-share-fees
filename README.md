# A-share fee-model excerpt

I use this small, adapted piece of my personal `worldquant_101` research project to make trading costs explicit before interpreting a strategy result. It starts with daily buy and sell turnover weights from trades that have already filled, then breaks the fees into stamp duty, brokerage, transfer, and securities-management costs as fractions of portfolio value. The tests use synthetic turnover. There is no market data or performance result in this repository.

The sample supports trade dates from January 2023 onward. Seller stamp duty is 10 basis points before August 28, 2023, and 5 basis points from that date, following the [Ministry of Finance announcement](https://m.mof.gov.cn/czxw/202308/t20230827_3904226.htm). Brokerage (2.5 basis points), transfer (0.1), and securities management (0.2) are fixed illustrative assumptions, not broker quotes or a complete historical schedule.

To run the tests, install `requirements.txt` in a Python environment and run:

```sh
python -m unittest discover -s tests -v
```

This is a fee-model excerpt, not a complete backtester or a reproduction of my Juhan Fund LightGBM result. It does not decide whether an order fills or model slippage, market impact, minimum commissions, lot rules, suspensions, price limits, or T+1 settlement.
