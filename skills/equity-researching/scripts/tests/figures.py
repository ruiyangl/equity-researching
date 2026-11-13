"""The published numbers the tests compare dcf.py against."""

# Chapter 2, Summary Illustration. No nonoperating assets or debt. One share,
# so that value per share equals shareholder value.
ILLUSTRATION = {
    "starting_sales": 100.0,
    "sales_growth_rate": 0.10,
    "operating_profit_margin": 0.15,
    "cash_tax_rate": 0.25,
    "incremental_fixed_capital_rate": 0.15,
    "incremental_working_capital_rate": 0.10,
    "cost_of_capital": 0.08,
    "continuing_value_method": "perpetuity_with_inflation",
    "inflation": 0.02,
    "nonoperating_assets": 0,
    "debt": 0,
    "shares_outstanding": 1,
    "forecast_years": 5,
}

# Table 2.1 as printed, years 1 to 5.
TABLE_2_1 = {
    "sales": [110.00, 121.00, 133.10, 146.41, 161.05],
    "operating_profit": [16.50, 18.15, 19.97, 21.96, 24.16],
    "cash_taxes": [4.13, 4.54, 4.99, 5.49, 6.04],
    "nopat": [12.38, 13.61, 14.97, 16.47, 18.12],
    "fixed_capital_investment": [1.50, 1.65, 1.82, 2.00, 2.20],
    "working_capital_investment": [1.00, 1.10, 1.21, 1.33, 1.46],
    "free_cash_flow": [9.88, 10.86, 11.95, 13.14, 14.46],
    "pv_free_cash_flow": [9.14, 9.31, 9.49, 9.66, 9.84],
    "cumulative_pv_free_cash_flow": [9.14, 18.46, 27.94, 37.60, 47.44],
}
TOTAL_INVESTMENT = [2.50, 2.75, 3.03, 3.33, 3.66]

# The authors' spreadsheet: shareholder value per share for forecast periods
# of 1 to 25 years (row 27 of its "Price Implied Expectations" sheet).
DOMINOS_VALUE_PER_SHARE = [
    285.184853, 303.249794, 321.596452, 340.229218, 359.152554,
    378.370993, 397.889135, 417.711654, 437.843298, 458.288887,
    479.053317, 500.141559, 521.558664, 543.309760, 565.400056,
    587.834841, 610.619488, 633.759452, 657.260274, 681.127582,
    705.367092, 729.984606, 754.986021, 780.377323, 806.164592,
]
# Two full columns of the same sheet: year 1 and year 8.
DOMINOS_YEAR_1 = {
    "sales": 3872.116, "operating_profit": 677.6203, "cash_taxes": 111.80735,
    "nopat": 565.812951, "fixed_capital_investment": 37.9974,
    "working_capital_investment": 25.3316, "free_cash_flow": 502.48395,
    "pv_free_cash_flow": 476.934566, "cumulative_pv_free_cash_flow": 476.934566,
    "pv_continuing_value": 14523.189383, "corporate_value": 15000.123949,
    "shareholder_value": 11222.023949,
}
DOMINOS_YEAR_8 = {
    "sales": 6217.772148, "operating_profit": 1088.110126, "cash_taxes": 179.538171,
    "nopat": 908.571955, "fixed_capital_investment": 61.015521,
    "working_capital_investment": 40.677014, "free_cash_flow": 806.87942,
    "pv_free_cash_flow": 531.497802, "cumulative_pv_free_cash_flow": 4030.352842,
    "pv_continuing_value": 16184.700759, "corporate_value": 20215.053601,
    "shareholder_value": 16436.953601,
}
