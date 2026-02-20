"""Phase 1: Fundamental Scoring Engine.

Implements Summers' fundamental screening framework (Standard Model, Section 4.2)
adapted for municipal bonds, integrating:
  - Bond extraction data (OS, financial reports, rating actions) from the corpus
  - Publicly-traded waste sector equity data (19 tickers with daily prices + financials)
  - EMMA secondary market trade data (199 CUSIPs)

The equity time series serves a dual role:
  1. Obligor credit signal — conduit revenue bonds are backed by publicly-traded
     waste companies (WM, RSG, GFL, CWST). Their equity fundamentals (leverage,
     profitability, momentum) provide a dense, daily-frequency complement to the
     sparse bond-side data.
  2. Sector benchmark — the full 19-ticker basket defines the waste sector's
     financial health envelope. Individual obligors are scored relative to sector
     peers, establishing the investable universe for Phase 2 (S_Omega calculation).
"""
