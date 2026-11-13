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


# ---------------------------------------------------------------------------
# Real companies: bank DCFs published in SEC merger filings ($ millions).
# Each holds management's projections and the bank's answer, as printed.
# ---------------------------------------------------------------------------

# NIC Inc., valued by Cowen for its sale to Tyler Technologies (2021).
# Proxy (DEFM14A, 2021-03-17), "Summary of the Projections" and "Discounted
# Cash Flow Analysis":
#   https://www.sec.gov/Archives/edgar/data/1065332/000114036121008824/nt10019848x8_defm14a.htm
# Supplement (DEFA14A, 2021-04-09), which adds the cash, debt and share count:
#   https://www.sec.gov/Archives/edgar/data/1065332/000114036121012312/brhc10022986_defa14a.htm
# Valuation date December 31, 2020, NIC's fiscal year end.
NIC = {
    "years": [2021, 2022, 2023, 2024, 2025],
    "revenue": [424.5, 496.8, 550.0, 613.9, 680.9],
    "ebit": [83.9, 101.4, 117.8, 139.2, 160.2],
    "taxes": [21.0, 25.4, 29.5, 34.8, 40.1],                 # "Assumed tax rate of 25.0%"
    "depreciation_and_amortization": [15.7, 14.1, 13.5, 12.8, 12.9],
    "capital_expenditures": [13.3, 12.4, 12.9, 13.5, 13.6],  # incl. capitalized software
    "change_in_working_capital": [0.0, 0.0, 0.0, 0.0, 0.0],
    "unlevered_free_cash_flow": [65.3, 77.7, 88.9, 103.6, 119.4],
    "cash": 236.5,                       # "approximately $236.5 million"
    "debt": 0.0,
    "diluted_shares": 67.4,              # "approximately 67.4 million"
    # Perpetuity growth 2.5% to 3.5% on 2025 free cash flow; discount rates
    # 8.0% to 9.0%: "$26.80 to $36.53 per share".
    "answers": [
        {"cost_of_capital": 0.09, "growth": 0.025, "value_per_share": 26.80},
        {"cost_of_capital": 0.08, "growth": 0.035, "value_per_share": 36.53},
    ],
}

# Pre-Paid Legal Services, valued by Berenson for its sale to MidOcean (2011).
# Proxy (DEFM14A, 2011-05-13), "Prospective Financial Information" and
# "Opinion of Berenson":
#   https://www.sec.gov/Archives/edgar/data/311657/000120677411001216/prepaid_defm14a.htm
# "utilizing end of period discounting"; cash and debt as of December 31, 2010,
# the fiscal year end. Whole $ millions as printed. Depreciation is EBITDA
# minus EBIT. Signs follow the table: (4) for working capital and 1 for
# "Sale/(Purchase) of Available for Sale Investments" are cash flows, the
# reading that reproduces the published range.
PRE_PAID_LEGAL = {
    "years": [2011, 2012, 2013, 2014, 2015],
    "revenue": [450, 458, 471, 491, 517],
    "ebitda": [115, 115, 114, 114, 116],
    "ebit": [107, 108, 108, 108, 110],
    "taxes": [42, 42, 43, 43, 43],                           # "Pre-Interest Income Tax Expense"
    "capital_expenditures": [5, 5, 5, 5, 5],
    "working_capital_cash_flow": [-4, 0, 0, 0, 1],
    "investments_sold_cash_flow": [1, 0, -1, -1, -1],
    "cash": 47.7,                        # "approximately $47.7 million of unrestricted cash"
    "debt": 0.9,                         # "$0.9 million of debt (including capital lease payables)"
    "diluted_shares": 9.8,               # "approximately 9.8 million shares"
    # Perpetuity growth (2.00)% to 2.00% on 2015 free cash flow; discount
    # rates 12.00% to 15.00%: "approximately $47.25 to $69.00".
    "answers": [
        {"cost_of_capital": 0.15, "growth": -0.02, "value_per_share": 47.25},
        {"cost_of_capital": 0.12, "growth": 0.02, "value_per_share": 69.00},
    ],
}


# Mid-year discounting ($ millions).

# Cornerstone Building Brands, valued by Centerview for its sale to CD&R (2022).
# Proxy (DEFM14A, 2022-05-24), Centerview's "Discounted Cash Flow Analysis":
#   https://www.sec.gov/Archives/edgar/data/883902/000110465922064226/tm228519-14_defm14a.htm
# Centerview's board book (SC 13E3/A exhibit (c)(7), 2022-05-10), page 18, with
# the free cash flow build and the price grid:
#   https://www.sec.gov/Archives/edgar/data/883902/000110465922057808/tm228519d12_ex99-c7.htm
# "discounting to present value as of December 31, 2021 ... and the mid-year
# convention"; only discounting the continuing value mid-year too fits the
# grid. Debt and cash are the board book's, from its offer summary ("Less:
# Cash (394) Plus: Debt 3,081").
#
# The share count is the one the board book prints, "Diluted Shares
# Outstanding ... 133.7", used for every price: the proxy says Centerview
# divided by "the number of fully-diluted outstanding shares as of February
# 22, 2022".
#
# The board book prints every input rounded to $1mm, so the prices carry two
# roundings: their own, to the nearest $0.25, and that of the inputs. The
# second can move a price by up to $0.071 (at 10% and 2.5%): the terminal
# free cash flow +/- $0.5mm moves the value by $4.5mm, each year's free cash
# flow +/- $1mm (it is rebuilt from rounded lines: 2026 adds up to 583
# against 582 printed) by $4.0mm, and debt and cash +/- $0.5mm each by $1mm;
# $9.4mm over 133.7mm shares is $0.071. Eight of the nine prices are within
# $0.125 regardless; $20.50 is $0.154 out.
CORNERSTONE = {
    "years": [2022, 2023, 2024, 2025, 2026],
    "revenue": [6428, 6766, 6778, 6857, 7175],
    "ebit": [453, 581, 632, 690, 793],
    "taxes": [136, 174, 190, 207, 238],
    "depreciation_and_amortization": [276, 252, 227, 203, 179],
    "working_capital_cash_flow": [199, 9, 65, 54, 28],       # "Plus / (Less): Change in NWC"
    "capital_expenditures": [161, 169, 169, 171, 179],
    "cash_settlement": [53, 0, 0, 0, 0],                      # "Cash Settlement (tax adj.)"
    "free_cash_flow": [684, 499, 565, 569, 582],
    "terminal_free_cash_flow": 575,      # terminal year: D&A equal to capex, NWC +21
    "cash": 394,
    "debt": 3081,
    "discounting": "mid_year_including_continuing_value",
    "diluted_shares": 133.7,
    "price_rounding": 0.25,              # "rounded to the nearest $0.25"
    "input_rounding": 0.071,             # the most the inputs' rounding moves a price
    # Discount rates 10.0% to 12.5% by perpetuity growth 1.75% to 2.5%; the
    # middle column is printed "2.13%", the midpoint 2.125% rounded.
    "answers": [
        {"cost_of_capital": r, "growth": g, "value_per_share": price}
        for r, row in ((0.10, (31.75, 33.50, 35.50)),
                       (0.1125, (25.25, 26.50, 28.00)),
                       (0.125, (20.50, 21.25, 22.25)))
        for g, price in zip((0.0175, 0.02125, 0.025), row)
    ],
}


# ---------------------------------------------------------------------------
# Published worked examples, matched to full precision: the cached cell values
# of free spreadsheets. Only the numbers are copied here, with their sources.
# ---------------------------------------------------------------------------

# Gateway, April 21, 2000: the authors' first-edition price-implied
# expectations spreadsheet ("Price Implied Expectations.xls", from the book's
# site, now in the Wayback Machine):
#   http://web.archive.org/web/20040409215510/http://www.expectationsinvesting.com:80/spreadsheets/Price%20Implied%20Expectations.xls
# Sheet "Inputs" (C6 to C31) and sheet "Price Implied Expectations".
GATEWAY = {
    "company": "Gateway",
    "base_year": 1999,
    "starting_sales": 8645.561,
    "sales_growth_rate": 0.2,
    "operating_profit_margin": 0.09,
    "cash_tax_rate": 0.35,
    "incremental_fixed_capital_rate": 0.11,
    "incremental_working_capital_rate": -0.05,
    "cost_of_capital": 0.1,
    "continuing_value_method": "perpetuity_with_inflation",
    "inflation": 0.02,
    "nonoperating_assets": {"cash": 1127.654, "marketable_securities": 208.717},
    "debt": {"debt": 2.998, "capitalized_operating_leases": 0.0,
             "employee_stock_options": 713.2612905743191},
    "shares_outstanding": 321.165,
    "share_price": 52.0,
}
# Row 27: value per share for forecast periods of 1 to 25 years. Cell C31,
# "Market-Implied Forecast Period", is 7: year 7 is worth 51.99, a cent under
# the $52 price.
GATEWAY_VALUE_PER_SHARE = [
    25.258905160950253, 28.80391984997046, 32.67120860162886,
    36.89006905798348, 41.4924622830976, 46.51325489231301,
    51.990483193275274, 57.96564133977958, 64.48399568142062,
    71.59492769048356, 79.3523080640068, 87.81490483512303,
    97.04682858543167, 107.11801813122288, 118.10477036299514,
    130.0903182522012, 143.1654614040624, 157.42925393336552,
    172.98975487442345, 189.964846810123, 208.48312892179527,
    228.68489122543772, 250.72317737486586, 274.76494408333286,
    300.9923259471152,
]
GATEWAY_MARKET_IMPLIED_YEARS = 7
GATEWAY_YEAR_1 = {
    "sales": 10374.6732,
    "operating_profit": 933.7205879999999,
    "cash_taxes": 326.80220579999997,
    "nopat": 606.9183822,
    "fixed_capital_investment": 190.20234199999996,
    "working_capital_investment": -86.45560999999998,
    "free_cash_flow": 503.17165020000004,
    "pv_free_cash_flow": 457.4287729090909,
    "cumulative_pv_free_cash_flow": 457.4287729090909,
    "pv_continuing_value": 7034.735793681818,
    "corporate_value": 7492.164566590909,
    "shareholder_value": 8112.276276016589,
    "value_per_share": 25.258905160950253,
}
GATEWAY_YEAR_7 = {
    "sales": 30978.608180428797,
    "operating_profit": 2788.0747362385914,
    "cash_taxes": 975.826157683507,
    "nopat": 1812.2485785550844,
    "fixed_capital_investment": 567.941149974528,
    "working_capital_investment": -258.15506817024,
    "free_cash_flow": 1502.4624967507964,
    "pv_free_cash_flow": 771.0008275448475,
    "cumulative_pv_free_cash_flow": 4220.293428538177,
    "pv_continuing_value": 11857.118396804397,
    "corporate_value": 16077.411825342573,
    "shareholder_value": 16697.523534768254,
    "value_per_share": 51.990483193275274,
}

# Wall Street Prep, "Financial Modeling Quick Lesson: Building a Simple DCF
# Model", sheet "Completed DCF Exercise". Year-end discounting; the terminal
# value is FCF_5 x (1+g)/(r-g).
#   https://media.wallstreetprep.com/uploads/2021/02/15191917/Wall-Street-Prep-Financial-Modeling-Quick-Lesson-DCFql.xls
WSP_QUICK_LESSON = {
    "revenue_2012": 6000.0,                                         # E10
    "growth": [0.1, 0.11, 0.12, 0.13, 0.13],                        # F11:J11
    "ebit_margin": 0.3,                                             # F17:J17
    "tax_rate": 0.4,                                                # F51:J51
    "depreciation_and_amortization": [                              # F53:J53
        369.6000000000001, 388.2780000000001, 336.4099200000001,
        435.7739232000001, 460.9931800320001],
    "capital_expenditures_cash_flow": [                             # F59:J59
        -53.5, -64.73500000000001, -78.3882000000001,
        -95.11101599999995, -107.47544807999986],
    "working_capital_cash_flows": [                                 # F54:J58
        [-135.00000000000023, -163.35000000000014, -197.80200000000013, -239.9997599999997, -271.1997287999998],
        [-14.024999999999864, -52.19637499999999, -91.1111451249999, -108.1409194923749, -118.84687052212007],
        [-14.700000000000003, -16.773900000000012, -16.609928399999987, -16.00089769199998, -21.279963092076002],
        [14.999999999999886, 55.82499999999993, 97.44507499999986, 115.65873742500003, 127.10895243007485],
        [9.300000000000011, 11.253000000000014, 13.62636000000002, 16.53331679999998, 18.682647984],
    ],
    "ebiat": [1188.0, 1318.6800000000003, 1476.9216000000004,       # F52:J52
              1668.9214080000004, 1885.8811910400004],
    "unlevered_free_cash_flow": [                                   # F60:J60
        1364.675, 1476.9807250000003, 1540.4916814750002,
        1777.6347922406258, 1973.8639609918796],
    "pv_free_cash_flow": [                                          # F62:J62
        1218.615721094383, 1177.7413130162195, 1096.9124868060962,
        1130.2973400415735, 1120.7401289394636],
    "wacc": 0.11985671641791046,                                    # D88
    "long_term_growth": 0.04,                                       # C67
    "cash": 1500.0, "debt": 4250.0, "diluted_shares": 500.0,        # E25, E33, D5
    "pv_terminal_value": 14595.763341900012,                        # C71
    "enterprise_value": 20340.070331797746,                         # D91
    "value_per_share": 35.180140663595495,                          # D95
}

# Wall Street Prep, "Terminal Growth Rate" template, sheet "Model": free cash
# flow mid-year (G8 = G5/(1+G9)^(G3-0.5)), terminal value at year 5
# (F16 = F15/(1+G9)^K3): the "mid_year" option.
#   https://media.wallstreetprep.com/uploads/2023/12/28013934/WSP-Terminal-Growth-Rate_vF.xlsx
WSP_TERMINAL_GROWTH = {
    "free_cash_flow_0": 60,                                         # F5
    "growth": [0.06, 0.05, 0.04, 0.035, 0.03],                      # G6:K6
    "wacc": 0.08,                                                   # G9
    "terminal_growth": 0.025,                                       # F13
    "pv_free_cash_flow": [                                          # G8:K8
        61.199128534100325, 59.499152741486427, 57.295480417727667,
        54.908168733655671, 52.366123884875321],
    "pv_terminal_value": 939.07380649647905,                        # F16
    "enterprise_value": 1224.3418608083243,                         # F17
}

# Edward Bodmer, "Proof-of-Timing-in-DCF-Model.xlsx", sheet "Simple Case",
# linked from https://edbodmer.com/partial-year-discounting-and-timing-in-dcf-analysis/
#   https://edbodmer.com/wp-content/uploads/2019/03/Proof-of-Timing-in-DCF-Model.xlsx
# Free cash flow of 100 grows 20% a year; the forecast is 2016 to 2021, so
# 2015's 144 is year 0. The year-end value (F46, Excel's NPV) is moved half a
# year by F48 = F46*(1+WACC)^0.5, continuing value included: the
# "mid_year_including_continuing_value" option.
BODMER = {
    "free_cash_flow_0": 144,                                        # H29
    "growth": 0.2,                                                  # E6
    "long_term_growth": 0.03,                                       # E7
    "wacc": 0.1,                                                    # E15
    "years": 6,                                                     # E9:E10, 2016 to 2021
    "pv_free_cash_flow_year_end": 1184.5614935077024,               # F44
    "pv_terminal_value_year_end": 3571.3551646582523,               # F45
    "enterprise_value_year_end": 4755.9166581659547,                # F46
    "enterprise_value_mid_year": 4988.0474722442714,                # F48
}
