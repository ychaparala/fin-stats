import argparse
import logging

import emoji
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

logging.basicConfig(level=logging.INFO)


def arg_parser():
    parser = argparse.ArgumentParser(
        description="Utility to analyse financial statements"
    )
    parser.add_argument(
        "--analyse-stocks-financial-statements",
        help="Provide stocks to analyse their financial statements",
        required=False,
    )
    parser.add_argument("--year", help="Provide financial year", required=False)
    parser.add_argument(
        "--credits",
        help="Credits for fin-stat utility",
        required=False,
        action="store_true",
    )
    return parser.parse_args()


def bang_for_buck(stock: yf.Ticker):
    profitability = (
        stock.financials.loc["Net Income"].iloc[::-1]
        / stock.financials.loc["Total Revenue"].iloc[::-1]
    )
    asset_turn_over = (
        stock.financials.loc["Total Revenue"].iloc[::-1]
        / stock.balance_sheet.loc["Total Assets"].iloc[::-1].rolling(window=2).mean()
    )
    financial_leverage = (
        stock.balance_sheet.loc["Total Assets"].iloc[::-1].rolling(window=2).mean()
        / stock.balance_sheet.loc["Total Stockholder Equity"]
        .iloc[::-1]
        .rolling(window=2)
        .mean()
    )
    return_on_equity = profitability * asset_turn_over * financial_leverage
    return {
        "name": stock.ticker,
        "profitability": profitability,
        "asset_turn_over": asset_turn_over,
        "financial_leverage": financial_leverage,
        "return_on_equity": return_on_equity,
    }


def cash_conversion_cycle(stock: yf.Ticker):
    try:
        inventory_turn_over_days = 365 / (
            stock.financials.loc["Cost Of Revenue"].iloc[::-1]
            / stock.balance_sheet.loc["Inventory"].iloc[::-1].rolling(window=2).mean()
        )
        accounts_receivable_turn_over_days = 365 / (
            stock.financials.loc["Total Revenue"].iloc[::-1]
            / stock.balance_sheet.loc["Net Receivables"]
            .iloc[::-1]
            .rolling(window=2)
            .mean()
        )
        accounts_payable_turn_over_days = 365 / (
            stock.financials.loc["Cost Of Revenue"].iloc[::-1]
            / stock.balance_sheet.loc["Accounts Payable"]
            .iloc[::-1]
            .rolling(window=2)
            .mean()
        )
        return {
            "name": stock.ticker,
            "cash_conversion_cycle": inventory_turn_over_days
            + accounts_receivable_turn_over_days
            - accounts_payable_turn_over_days,
        }
    except Exception as e:
        return {"name": stock.ticker, "cash_conversion_cycle": 0}


def liquidity_and_solvency(stock: yf.Ticker):
    liabilities_to_equity = (
        stock.balance_sheet.loc["Total Liab"].iloc[::-1]
        / stock.balance_sheet.loc["Total Stockholder Equity"].iloc[::-1]
    )
    interest_coverage_ratio = (
        stock.financials.loc["Ebit"].iloc[::-1]
        / stock.financials.loc["Interest Expense"].iloc[::-1]
    )
    current_ratio = (
        stock.balance_sheet.loc["Total Current Assets"].iloc[::-1]
        / stock.balance_sheet.loc["Total Current Liabilities"].iloc[::-1]
    )
    quick_ratio = (
        stock.balance_sheet.loc["Cash"].iloc[::-1]
        + stock.balance_sheet.loc["Short Term Investments"].iloc[::-1]
        + stock.balance_sheet.loc["Net Receivables"].iloc[::-1]
    ) / stock.balance_sheet.loc["Total Current Liabilities"].iloc[::-1]

    return {
        "name": stock.ticker,
        "liquidity": {"current_ratio": current_ratio, "quick_ratio": quick_ratio},
        "solvency": {
            "liabilities_to_equity": liabilities_to_equity,
            "interest_coverage_ratio": interest_coverage_ratio,
        },
    }

def equity_analysis(stock: yf.Ticker):
    return {
        "name": stock.ticker,
        "pe": stock.info['forwardPE']
    }


def cash_conversion_cycle_df(stocks, year):
    p = {}
    i = ["cash_conversion_cycle"]
    try:
        for s in stocks:
            if year is None:
                year = str(s["cash_conversion_cycle"].index.max().year)
            p[s["name"]] = s["cash_conversion_cycle"].loc[year].values[0]
        logging.info(f"Cash conversion cycle: {p}")
    except Exception as e:
        p[s["name"]] = 0
    return pd.DataFrame(p, index=i).transpose()


def bang_for_buck_df(stocks, year):
    p = {}
    i = ["profitability", "asset_turn_over", "financial_leverage", "return_on_equity"]
    for s in stocks:
        if year is None:
            year = str(s["profitability"].index.max().year)
        p[s["name"]] = [
            s["profitability"].loc[year].values[0],
            s["asset_turn_over"].loc[year].values[0],
            s["financial_leverage"].loc[year].values[0],
            s["return_on_equity"].loc[year].values[0],
        ]
    logging.info(f"Bang for the buck analysis: {p}")
    return pd.DataFrame(p, index=i).transpose()


def liquidity_and_solvency_df(stocks, year):
    p = {}
    i = [
        "current_ratio",
        "quick_ratio",
        "liabilities_to_equity",
        "interest_coverage_ratio",
    ]
    for s in stocks:
        if year is None:
            year = str(s["liquidity"]["current_ratio"].index.max().year)
        p[s["name"]] = [
            s["liquidity"]["current_ratio"].loc[year].values[0],
            s["liquidity"]["quick_ratio"].loc[year].values[0],
            s["solvency"]["liabilities_to_equity"].loc[year].values[0],
            s["solvency"]["interest_coverage_ratio"].loc[year].values[0],
        ]
    logging.info(f"Liquidity and Solvency: {p}")
    return pd.DataFrame(p, index=i).transpose()

def equity_analysis_df(stocks):
    p = {}
    i = ["PE"]
    for s in stocks:
        p[s["name"]] = s["pe"]
    logging.info(f"Equity Analysis: {p}")
    return pd.DataFrame(p, index=i).transpose()

def plot(b_df, c_df, l_df, e_df):
    fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(16, 9))
    fig.suptitle("Financial Statements Analysis")
    b_df.plot(
        ax=axs[0,0], kind="bar", title="Bank for the Buck", xlabel="Stocks", ylabel="Ratios"
    )
    c_df.plot(
        ax=axs[0,1],
        kind="bar",
        title="Cash Conversion",
        xlabel="Stocks",
        ylabel="Number of Days",
    )
    l_df.plot(
        ax=axs[1,0],
        kind="bar",
        title="Liquidity and Solvency",
        xlabel="Stocks",
        ylabel="Ratios",
    )
    e_df.plot(
        ax=axs[1,1],
        kind="bar",
        title="Equity Analysis",
        xlabel="Stocks",
        ylabel="Price to Earnings",
    )
    plt.show()


def plot_sankey_earnings():
    pass


def app():
# if __name__ == "__main__":
    args = arg_parser()
    if args.analyse_stocks_financial_statements:
        logging.info(
            f"Analyzing financial statements for: {args.analyse_stocks_financial_statements.upper()}"
        )
        bank_for_buck_res = []
        cash_conversion_cycle_res = []
        liquidity_and_solvency_res = []
        equity_analysis_res = []
        tickers = args.analyse_stocks_financial_statements.upper().split(",")
        stocks = []
        for t in tickers:
            stocks.append(yf.Ticker(t))
        for stock in stocks:
            bank_for_buck_res.append(bang_for_buck(stock))
            cash_conversion_cycle_res.append(cash_conversion_cycle(stock))
            liquidity_and_solvency_res.append(liquidity_and_solvency(stock))
            equity_analysis_res.append(equity_analysis(stock))
        b_df = bang_for_buck_df(bank_for_buck_res, args.year)
        c_df = cash_conversion_cycle_df(cash_conversion_cycle_res, args.year)
        l_df = liquidity_and_solvency_df(liquidity_and_solvency_res, args.year)
        e_df = equity_analysis_df(equity_analysis_res)
        plot(b_df, c_df, l_df, e_df)
    elif args.credits:
        print(
            emoji.emojize(
                """
:tangerine:  ████████ ███████  █████  ███    ███      ██████  ██████   █████  ███    ██  ██████  ███████   :tangerine:
:tangerine:     ██    ██      ██   ██ ████  ████     ██    ██ ██   ██ ██   ██ ████   ██ ██       ██        :tangerine:
:tangerine:     ██    █████   ███████ ██ ████ ██     ██    ██ ██████  ███████ ██ ██  ██ ██   ███ █████     :tangerine:
:tangerine:     ██    ██      ██   ██ ██  ██  ██     ██    ██ ██   ██ ██   ██ ██  ██ ██ ██    ██ ██        :tangerine:
:tangerine:     ██    ███████ ██   ██ ██      ██      ██████  ██   ██ ██   ██ ██   ████  ██████  ███████   :tangerine:                                                                                                                                                                  
"""
            )
        )
