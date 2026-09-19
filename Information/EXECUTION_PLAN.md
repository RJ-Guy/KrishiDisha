# KrishiDisha — Complete Technical Execution Plan & Product Blueprint

> **Smart India Hackathon (SIH) 2026**  
> **Problem Statement ID:** 26132  
> **Problem Statement Title:** Strengthening market linkages and price discovery for farmers  
> **Theme:** Agriculture, FoodTech & Rural Development  
> **Category:** Software  
> **Team Name:** MakhanChor (IIIT Sri City / IIITS)  
> **Product Name:** **KrishiDisha (KRISHI-DISHA)**  
> **Primary Purpose:** Master specification and execution blueprint for building the end-to-end AI-powered farmer/FPO market-intelligence, price forecasting, net-realization optimization, buyer-linkage, and digital transaction platform.

---

## Executive Summary & Core Philosophy

### Core USP
> **"We don't optimize for the highest price. We optimize for the farmer's highest NET REALIZATION."**

### Final Product Positioning
> *"Our platform moves the farmer from price awareness to decision intelligence — predicting where prices may move, identifying suitable buyers, estimating the cost of reaching them, and recommending the selling option with the best expected net realization."*

---

## Table of Contents
1. [Product Definition & Scope](#1-product-definition--scope)
2. [End-to-End Product Workflow](#2-end-to-end-product-workflow)
3. [The Five Core Engines](#3-the-five-core-engines)
4. [Mathematical Formulation & Decision Economics](#4-mathematical-formulation--decision-economics)
5. [Market Linkage, Bulk Aggregation & Reverse Marketplace](#5-market-linkage-bulk-aggregation--reverse-marketplace)
6. [Transaction Lifecycle, Logistics & Trust Modules](#6-transaction-lifecycle-logistics--trust-modules)
7. [System Architecture & Data Flow](#7-system-architecture--data-flow)
8. [Machine Learning Pipeline & Forecast Service](#8-machine-learning-pipeline--forecast-service)
9. [Database Schema (PostgreSQL)](#9-database-schema-postgresql)
10. [API Contracts & Endpoints](#10-api-contracts--endpoints)
11. [Frontend Architecture & Dashboards](#11-frontend-architecture--dashboards)
12. [Project Directory & Code Organization](#12-project-directory--code-organization)
13. [Feasibility, Viability & Strategic Impact](#13-feasibility-viability--strategic-impact)
14. [Research, Literature & Data Citations](#14-research-literature--data-citations)
15. [Antigravity Phased Development Roadmap (Phases 0–10)](#15-antigravity-phased-development-roadmap-phases-010)
16. [Antigravity Agent Prompt Sequence](#16-antigravity-agent-prompt-sequence)
17. [Complete 16-Step Demonstration Scenario](#17-complete-16-step-demonstration-scenario)
18. [Critical Implementation Rules & Checklist](#18-critical-implementation-rules--checklist)

---

## 1. Product Definition & Scope

### 1.1 Goal
Empower farmers, Farmer Producer Organizations (FPOs), and agricultural sellers to decide **where, when, and to whom to sell** in order to achieve the highest realistic net financial return, eliminating reliance on middlemen rumours and avoiding distress sales.

### 1.2 System Inputs
* **Farmer / FPO Lot Parameters:** Crop commodity, variety, quantity, physical location (GPS / Mandi proximity), harvest timing / expected selling period, quality grade, moisture percentage, and storage availability.
* **Current Market Data:** Live Mandi prices and arrivals from `data.gov.in` / Agmarknet / e-NAM.
* **Historical Data:** Longitudinal price, arrival, and seasonal records for trend discovery and machine learning.
* **Buyer Demand:** Real-time buyer requirements, purchase price offers, quantity needs, acceptable quality grades, delivery windows, and location constraints.
* **Logistics & Infrastructure:** Distances, vehicle capacities, estimated transport rates, and nearby storage facilities with associated holding costs.
* **Procurement Information:** Minimum Support Price (MSP) benchmarks, state procurement center availability, and eligibility criteria.

### 1.3 System Outputs
* Current price comparison across nearby and regional mandis.
* Short-term price forecasts with confidence intervals and directional trends (Up / Down / Stable).
* Verified buyer matches and reverse marketplace match scoring.
* Granular logistics, storage, and handling cost breakdown.
* Expected Net Realization comparison across all selling channels.
* Clear, actionable **SELL NOW / WAIT / BEST BUYER** recommendation.
* Complete digital transaction tracking, delivery validation, payment confirmation, and expected-vs-actual feedback analytics.

---

## 2. End-to-End Product Workflow

```
Farmer/FPO Input
       │
       ▼
Market Intelligence (Live & Historical Mandi Prices)
       │
       ▼
AI Price Forecast (7-day / short-term trend & confidence range)
       │
       ▼
Selling Opportunities Discovery
       │
       ▼
Bulk Aggregation Check (Can lot combine with nearby lots?)
       │
       ▼
Buyer Matching & Reverse Marketplace (Hard filters + Multi-factor score)
       │
       ▼
Digital Offer & Negotiation (Counter-offer / Acceptance)
       │
       ▼
Logistics & Storage Cost Estimation (OSRM route & transport rates)
       │
       ▼
Expected Net Realization Calculation
       │
       ▼
Decision Engine Recommendation (SELL NOW vs. WAIT vs. BEST BUYER)
       │
       ▼
Deal Acceptance & Digital Lot Reservation
       │
       ▼
Dispatch & Delivery
       │
       ▼
Quality & Quantity Confirmation at Receiving Hub
       │
       ▼
Payment Processing (PENDING ➔ PAID)
       │
       ▼
Actual Net Realization Calculation & Variance Recording
       │
       ▼
Feedback Loop & Model Calibration
```

---

## 3. The Five Core Engines

### 3.1 Market Intelligence Engine
* Fetches, standardizes, and presents live and historical market prices, arrivals, and demand trends across local, district, and regional mandis.
* Consolidates multi-source agricultural feeds into a unified schema for real-time comparison.

### 3.2 AI Forecasting Engine
* Ingests chronological historical series and engineered temporal/seasonal features.
* Produces short-term price predictions (e.g., 7-day horizon) formatted as a **forecast range + trend indicator + confidence score**, rather than misleading pinpoint guarantees.

### 3.3 Decision Engine
* Synthesizes forecast predictions with real-world economic constraints:
  * Holding/storage costs per day
  * Perishability and storage risk factors
  * Immediate farmer liquidity needs
  * Transport cost differentials between markets
  * Buyer availability and reliability metrics
* Outputs clear advice: **SELL NOW** (if holding costs or price drops exceed expected gains), **WAIT** (if price trajectory compensates for storage/risk), or **BEST BUYER / BEST MANDI** (where net realization is maximized).

### 3.4 Buyer & Bulk Engine
* Evaluates individual farm lots against active buyer tenders via hard filtering (commodity, grade, moisture, distance) and multi-factor ranking.
* **Bulk Aggregator:** Aggregates small, fragmented lots from multiple smallholder farmers into standardized bulk commercial lots to attract institutional buyers and negotiate better freight rates.

### 3.5 Logistics & Net Realization Engine
* Computes real route distances using OpenStreetMap / OSRM services.
* Translates gross commodity values into actual net retained income by subtracting transport, loading/unloading, storage, and platform handling costs.

---

## 4. Mathematical Formulation & Decision Economics

### 4.1 Net Realization Formula

The primary metric of the platform is **Net Realization**, defined as:

$$\text{Expected Net Realization} = \text{Expected Gross Selling Revenue} - \text{Logistics Cost} - \text{Storage Cost} - \text{Handling Cost} - \text{Applicable Deductions}$$

$$\text{Gross Revenue} = \text{Quantity (Quintals)} \times \text{Price per Quintal}$$

#### Worked Numerical Example:
* **Quantity:** 100 Quintals (Q) of Wheat
* **Headline Market Price:** ₹2,580 / Q
* **Gross Revenue:** $100 \times 2,580 = ₹2,58,000$
* **Transport Cost:** ₹1,500
* **Storage Cost:** ₹500
* **Handling / Labor:** ₹300
* **Expected Net Realization:**
  $$₹2,58,000 - (₹1,500 + ₹500 + ₹300) = ₹2,55,700$$

> **Core Rule:** The platform ranks selling options, mandis, and buyers by **Economic Net Outcome**, never by headline price alone. A mandi offering ₹2,600/Q with ₹10,000 transport will rank lower than a local mandi offering ₹2,560/Q with ₹1,000 transport.

### 4.2 SELL vs. WAIT Decision Logic

$$\Delta_{\text{price}} = \text{Forecast Price}(t + \Delta t) - \text{Current Price}(t)$$
$$\text{Cost}_{\text{waiting}} = (\text{Storage Cost/day} \times \Delta t) + \text{Risk Penalty}(\text{Perishability}, \text{Confidence Score})$$

* **SELL NOW** is recommended if:
  $$\Delta_{\text{price}} \le \text{Cost}_{\text{waiting}} \quad \text{OR} \quad \text{Liquidity Urgency} = \text{HIGH}$$
* **WAIT** is recommended only if:
  $$\Delta_{\text{price}} > \text{Cost}_{\text{waiting}} \quad \text{AND} \quad \text{Storage Available} = \text{TRUE} \quad \text{AND} \quad \text{Forecast Confidence} \ge \text{Threshold}$$

### 4.3 Expected vs. Actual Net Variance Analysis

$$\text{Variance}_{\text{Revenue}} = \text{Actual Net Realization} - \text{Expected Net Realization}$$

After physical fulfillment, actual weighed quantity, verified grade adjustments, and actual freight deductions are recorded. Variances are logged to refine future estimation algorithms.

---

## 5. Market Linkage, Bulk Aggregation & Reverse Marketplace

### 5.1 Digital Lot Specification
A standardized entity created by a Farmer or FPO:
* `lot_id`: Unique lot identifier
* `crop` & `variety`: e.g., Wheat (Sharbati)
* `quantity`: in Quintals
* `quality_metrics`: Grade (A/B/C), Moisture content (%), Foreign matter (%)
* `harvest_date`: Harvest / packaging date
* `location`: Mandi / Village GPS coordinates
* `storage_state`: Farm-stored / Warehouse / Freshly harvested
* `delivery_window`: Earliest and latest fulfillment dates

### 5.2 Multi-Factor Buyer Matching & Scoring
Buyers are scored using a weighted algorithm:

$$\text{Score} = w_1 \cdot S_{\text{price}} + w_2 \cdot S_{\text{distance}} + w_3 \cdot S_{\text{quality\_fit}} + w_4 \cdot S_{\text{reliability}} + w_5 \cdot S_{\text{volume\_compatibility}}$$

* **Hard Filters:** Incompatible commodity, quality below required threshold (e.g., Moisture > 12% when buyer requires $\le 12\%$), and out-of-bounds delivery window immediately disqualify a buyer.
* **Scoring Explanation:** The dashboard returns the match score accompanied by human-readable explanations (e.g., *"Matched 94%: Competitive offer ₹2,620, buyer is 18 km away, 98% on-time payment track record"*).

### 5.3 Reverse Marketplace
Large food processors, millers, and institutional buyers post tender requirements:
* Example: *"Wheat, Grade A, Moisture $\le 12\%$, 500 Quintals, delivery within 10 days to Central Silo."*
* The system automatically scans active farmer and FPO digital lots to determine if a single producer or a cluster can fulfill the order.

### 5.4 Bulk Aggregation Model
Smallholder farmers frequently cannot access premium institutional buyers due to minimum order volume thresholds.
* **Aggregation Example:**
  $$\text{Farmer A (30Q)} + \text{Farmer B (45Q)} + \text{Farmer C (80Q)} + \text{Farmer D (25Q)} + \text{Farmer E (70Q)} = \text{Aggregated Bulk Lot (250Q)}$$
* **Traceability Constraint:** Full origin traceability is preserved. Each farmer's share, moisture test, and quantity are preserved in child lot records tied to the master aggregated lot.

---

## 6. Transaction Lifecycle, Logistics & Trust Modules

### 6.1 Digital Negotiation & Offers
1. **Offer Initiation:** Buyer makes an offer on a Digital Lot (or Farmer quotes on a Reverse Marketplace tender).
2. **Counter / Acceptance:** Farmer accepts, rejects, or counters with updated price/quantity terms.
3. **Contract Lock:** An accepted offer transitions into an immutable `Transaction`.

### 6.2 Transaction State Machine

```
[OFFER CREATED]
       │
       ▼
[COUNTER OFFER] (Optional iterative cycle)
       │
       ▼
[OFFER ACCEPTED]
       │
       ▼
[LOT READY FOR PICKUP / DISPATCH]
       │
       ▼
[DISPATCHED / IN TRANSIT]
       │
       ▼
[DELIVERED AT DESTINATION]
       │
       ▼
[QUALITY & QUANTITY CONFIRMED]
       │
       ▼
[PAYMENT PENDING]
       │
       ▼
[PAYMENT RECEIVED]
       │
       ▼
[TRANSACTION COMPLETED]
```

* **Dispute Branch:** At any point after dispatch, if quality/quantity deviates or payment is withheld, state moves to `DISPUTED` and creates a `Grievance` record (`OPEN` $\rightarrow$ `UNDER REVIEW` $\rightarrow$ `RESOLVED` / `REJECTED`).

### 6.3 Logistics Engine & Bulk Routing
* Computes road distance between Farm/Collection Point and Mandi/Buyer Facility using OpenStreetMap / OSRM APIs.
* **Trip & Fleet Estimation:** Evaluates total volume against vehicle classes (e.g., Mini Truck 1.5T, Medium Truck 5T, Heavy Multi-axle 16T).
* Estimates cost using configurable per-km and per-quintal tariff baselines.
* **Bulk Consolidation:** Multi-farm collection points are routed to consolidated transport to minimize ton-kilometer freight expense.

### 6.4 Storage & MSP Benchmarking
* **Storage Module:** Shows accredited warehouses and cold-storage facilities within radius, including daily holding tariff, capacity, and estimated quality deterioration curve.
* **MSP Procurement Gateway:** Displays official Minimum Support Price benchmarks and nearest state procurement agency centers. Serves as a financial benchmark against open market bids.

### 6.5 Buyer Reliability Scoring
* Tracks verified platform history:
  * On-time payment rate: $\frac{\text{On-time Transactions}}{\text{Total Transactions}}$ (e.g., 46/50 = 92%).
  * Dispute frequency.
  * Acceptance-without-rejection rate.
* Reliability influences buyer ranking in search results.

---

## 7. System Architecture & Data Flow

```
   ┌────────────────────────────────────────────────────────────┐
   │                       FARMER / FPO                         │
   │               Web & Mobile Responsive UI                   │
   │       (React.js + Vite + Tailwind CSS + Recharts)          │
   └─────────────────────────────┬──────────────────────────────┘
                                 │ HTTP / JSON API Calls
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │                 FASTAPI BACKEND SERVICES                   │
   │                                                            │
   │  ┌──────────────────────┐        ┌──────────────────────┐  │
   │  │    Auth & Security   │        │ Market Intelligence  │  │
   │  │   (JWT / RBAC Roles) │        │   (Prices & Trends)  │  │
   │  └──────────────────────┘        └──────────────────────┘  │
   │  ┌──────────────────────┐        ┌──────────────────────┐  │
   │  │   Logistics Engine   │        │ Buyer & Bulk Matcher │  │
   │  │    (OSRM Distance)   │        │ (Reverse Mkt & Agg)  │  │
   │  └──────────────────────┘        └──────────────────────┘  │
   │  ┌──────────────────────┐        ┌──────────────────────┐  │
   │  │   Decision Engine    │        │ Transaction Engine   │  │
   │  │ (Net Realization/Wait│        │ (Offers/Escrow/State)│  │
   │  └──────────┬───────────┘        └──────────────────────┘  │
   └─────────────┼────────────────────────────────┬─────────────┘
                 │ Internal Model Calls           │ SQL Queries
                 ▼                                ▼
   ┌───────────────────────────┐      ┌─────────────────────────┐
   │    ML FORECAST SERVICE    │      │   POSTGRESQL DATABASE   │
   │  - Preprocessing & Scaler │      │  - Historical Prices    │
   │  - Lag/Moving Avg Features│      │  - Current Cache        │
   │  - Trained XGBoost Models │      │  - Users, Lots & Deals  │
   │  - Forecast + Uncertainty │      │  - Audit Logs & Feedback│
   └─────────────▲─────────────┘      └─────────────────────────┘
                 │
   ┌─────────────┴─────────────┐
   │    EXTERNAL DATA SOURCES  │
   │  - data.gov.in Live API   │
   │  - Kaggle Historical CSVs │
   │  - Agmarknet / e-NAM Feeds│
   └───────────────────────────┘
```

---

## 8. Machine Learning Pipeline & Forecast Service

### 8.1 Target Variable & Feature Engineering
* **Prediction Target:** Short-term future modal market price ($t+1$ to $t+7$ days) for a specified commodity, market/mandi, and variety context.
* **Engineered Feature Set:**
  * Price Lags: `lag_1`, `lag_3`, `lag_7`, `lag_14`, `lag_30`
  * Rolling Statistics: 7-day, 14-day, and 30-day moving averages and standard deviations (volatility)
  * Price Velocity & Acceleration: $\Delta p_{1d}$, $\Delta p_{7d}$
  * Arrival Features: Daily arrival quantities and rolling average arrivals (where available)
  * Categorical Encodings: State, District, Mandi, Commodity, Variety, Grade
  * Calendar & Seasonal Signals: Day of week, month, quarter, harvest season index

### 8.2 Model Development & Selection
1. **Baseline Model:** Simple Moving Average & Lag-1 persistence benchmark.
2. **Linear Baseline:** Ridge / Lasso Regression for linear coefficients.
3. **Ensemble Models:** Random Forest Regressor and XGBoost Regressor.
4. **Evaluation Metrics:** Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE), and Directional Accuracy (% of correct up/down predictions).
5. **Validation Strategy:** Strictly **Chronological Time-Series Splits** (Train on historical dates $T_0 \dots T_1$, validate on $T_1 \dots T_2$, test on unseen recent window $T_2 \dots T_3$). **Zero random splitting** to prevent future information leakage.

### 8.3 ML Pipeline Code Structure
```
backend/ml/
├── preprocessing.py    # Raw CSV ingestion, null handling, type conversion, standardization
├── features.py         # Shared feature extraction (used by BOTH training and live inference)
├── train.py            # Chronological split, baseline comparison, XGBoost training, hyperparameter tuning
├── evaluate.py         # Out-of-sample evaluation, MAE/RMSE calculation, residual plots
├── predict.py          # Production prediction service wrapper
└── model_artifacts/    # Serialized model (.joblib/.json), scalers, and metadata definitions
```

> **Strict Rule:** Training and live inference must import and execute the exact same `features.py` module to eliminate train-serve feature skew. Farmer API requests run inference on the pre-trained saved model artifact; farmer requests **never** trigger runtime model retraining.

---

## 9. Database Schema (PostgreSQL)

### 9.1 Core Entity Relationship Map
* `users` (id, email, password_hash, role, phone, created_at)
* `farmers` (id, user_id, state, district, village, pin_code, fpo_id)
* `fpos` (id, user_id, organization_name, registration_no, state, district)
* `buyers` (id, user_id, company_name, gst_no, reliability_score, verified)
* `commodities` (id, name, category, standard_unit)
* `markets` (id, market_name, state, district, latitude, longitude)
* `market_prices` (id, market_id, commodity_id, variety, arrival_date, min_price, max_price, modal_price, arrivals_volume)
* `lots` (id, owner_type, owner_id, commodity_id, variety, quantity_quintals, quality_grade, moisture_pct, location_lat, location_lng, status, created_at)
* `buyer_requirements` (id, buyer_id, commodity_id, required_quantity, max_price, min_grade, max_moisture, delivery_location_lat, delivery_location_lng, expiry_date)
* `offers` (id, lot_id, buyer_id, offered_price, quantity, counter_price, status, created_at, updated_at)
* `transactions` (id, offer_id, agreed_price, agreed_quantity, total_amount, transport_cost, storage_cost, net_realization, status, created_at)
* `logistics` (id, transaction_id, origin_address, destination_address, distance_km, estimated_cost, actual_cost, status)
* `storage_options` (id, facility_name, state, district, daily_cost_per_quintal, capacity_quintals, latitude, longitude)
* `procurement_options` (id, commodity_id, msp_price, agency_name, center_location, active)
* `payments` (id, transaction_id, amount, payment_status, payment_method, payment_date)
* `grievances` (id, transaction_id, raised_by_user_id, issue_type, description, status, resolution_notes)
* `forecasts` (id, commodity_id, market_id, forecast_date, horizon_days, predicted_modal_price, lower_bound, upper_bound, confidence_score, created_at)

---

## 10. API Contracts & Endpoints

All endpoints follow REST conventions and return structured JSON.

### 10.1 Authentication & Profile
* `POST /api/auth/register` — Register User (Roles: `FARMER`, `FPO`, `BUYER`, `ADMIN`)
* `POST /api/auth/login` — Authenticate and receive JWT Bearer token
* `GET /api/auth/me` — Current profile and permissions

### 10.2 Market Intelligence & Price Discovery
* `GET /api/market/prices` — Fetch filtered current mandi prices (`commodity`, `state`, `district`)
* `GET /api/market/trends` — Historical price and arrival series for visualization
* `GET /api/forecast` — Run price forecasting inference for a given commodity and market context

### 10.3 Lots & Marketplace
* `POST /api/lots` — Create digital lot listing
* `GET /api/lots` — Query active lots (supports filtering by commodity, grade, distance)
* `GET /api/lots/{id}` — Detailed lot profile with quality parameters
* `POST /api/lots/bulk-aggregate` — Combine multiple compatible child lots into a single master lot

### 10.4 Buyer Matching & Reverse Marketplace
* `GET /api/buyers` — List registered buyers
* `GET /api/buyers/match` — Ingests lot parameters; returns scored & ranked buyers with explanations
* `POST /api/buyer-requirements` — Buyers post tender requirements for reverse matching

### 10.5 Offers & Transactions
* `POST /api/offers` — Submit digital offer on a lot or tender
* `POST /api/offers/{id}/counter` — Submit counter-bid
* `POST /api/offers/{id}/accept` — Accept offer and initialize binding transaction
* `GET /api/transactions` — Query active and historical deals
* `GET /api/transactions/{id}` — Full transaction timeline, logistics status, and payment stage

### 10.6 Logistics, Storage & Decision Analytics
* `GET /api/logistics/estimate` — Calculate OSRM route distance, vehicle recommendation, and freight cost
* `GET /api/storage/nearby` — Query storage facilities with daily tariffs and distance
* `POST /api/decision/recommend` — Run Net Realization comparison and output **SELL NOW / WAIT / BEST BUYER** verdict

### 10.7 Payments, Reports & Grievances
* `GET /api/payments` — Query payment tracking records
* `POST /api/grievances` — Lodge transaction dispute with evidence
* `GET /api/reports/farmer-summary` — Download or display end-to-end deal realization and variance statement

---

## 11. Frontend Architecture & Dashboards

### 11.1 Tech Stack
* **Framework:** React.js (v18+) with Vite build tool
* **Styling:** Tailwind CSS + Lucide React icons
* **Data Visualization:** Recharts / Chart.js for interactive price trend charts, forecasting bands, and realization breakdowns
* **HTTP Client:** Centralized Axios instance (`src/services/api.js`) with request/response interceptors for JWT injection and unified error handling

### 11.2 Key Application Pages
1. **Authentication:** Login, Registration with Role Selection (`Farmer`, `FPO`, `Buyer`).
2. **Farmer / FPO Dashboard:** Overview cards for live prices, market trend, Sell/Wait advice, active lots, offers, and payment summary.
3. **Market Prices & Intelligence:** Mandi price browser, commodity filter, regional comparison table.
4. **Price Forecast & Analytics:** 7-day predictive chart with confidence range, historical overlay, and trend signals.
5. **Buyer Matching & Reverse Marketplace:** Ranked list of buyers, fit score badges, distance, direct offer creation.
6. **Bulk Lot Aggregation Hub:** FPO view to combine smallholder lots, review contribution shares, and publish bulk lots.
7. **Logistics & Net Realization Calculator:** Interactive map/distance calculator comparing multiple mandis/buyers net of freight.
8. **Deal Room & Transactions:** Offer counter-offer negotiation panel, live deal state tracker.
9. **Payments & Net Realization Report:** Expected-vs-actual variance report, payment receipts, dispute filing.

### 11.3 Modular Component Library
* `PriceCard` — Displays live modal price, daily change, and market name
* `ForecastChart` — Multi-line chart showing historical prices and bounded forecast interval
* `RecommendationCard` — High-visibility banner displaying SELL NOW, WAIT, or BEST BUYER with supporting rationale
* `NetRealizationCard` — Interactive cost breakdown (Gross price minus transport, storage, and handling)
* `BuyerCard` — Buyer profile, match score percentage, verification tag, and reliability index
* `LotCard` — Digital produce lot specifications, grade badges, and lot status
* `TransactionTimeline` — Horizontal step indicator showing progress from offer acceptance to final payment
* `PaymentStatusBadge` — Visual indicator (`PENDING`, `PARTIAL`, `PAID`, `DISPUTED`)

---

## 12. Project Directory & Code Organization

```
KrishiDisha/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── BuyerCard.jsx
│   │   │   ├── ForecastChart.jsx
│   │   │   ├── LotCard.jsx
│   │   │   ├── NetRealizationCard.jsx
│   │   │   ├── PriceCard.jsx
│   │   │   ├── RecommendationCard.jsx
│   │   │   └── TransactionTimeline.jsx
│   │   ├── hooks/
│   │   │   └── useAuth.js
│   │   ├── pages/
│   │   │   ├── BulkLotsPage.jsx
│   │   │   ├── BuyerDashboard.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── ForecastPage.jsx
│   │   │   ├── LogisticsPage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   ├── MarketPricesPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── ReportsPage.jsx
│   │   │   └── TransactionsPage.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── utils/
│   │   │   └── formatters.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── seed_data.py
│   │   ├── models/
│   │   │   ├── buyer.py
│   │   │   ├── grievance.py
│   │   │   ├── lot.py
│   │   │   ├── market.py
│   │   │   ├── transaction.py
│   │   │   └── user.py
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── buyers.py
│   │   │   ├── decision.py
│   │   │   ├── forecast.py
│   │   │   ├── logistics.py
│   │   │   ├── lots.py
│   │   │   ├── market.py
│   │   │   └── transactions.py
│   │   ├── schemas/
│   │   │   ├── auth_schema.py
│   │   │   ├── lot_schema.py
│   │   │   ├── market_schema.py
│   │   │   └── transaction_schema.py
│   │   ├── services/
│   │   │   ├── bulk_aggregation.py
│   │   │   ├── buyer_matching.py
│   │   │   ├── decision_engine.py
│   │   │   ├── logistics_service.py
│   │   │   ├── market_service.py
│   │   │   └── net_realization.py
│   │   ├── config.py
│   │   └── main.py
│   ├── ml/
│   │   ├── model_artifacts/
│   │   │   └── price_model.joblib
│   │   ├── evaluate.py
│   │   ├── features.py
│   │   ├── predict.py
│   │   ├── preprocessing.py
│   │   └── train.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── raw/
│   │   └── historical_mandi_prices.csv
│   └── processed/
│       └── cleaned_feature_matrix.csv
├── docker-compose.yml
└── README.md
```

---

## 13. Feasibility, Viability & Strategic Impact

### 13.1 Feasibility Dimensions
* **Technical Feasibility:** Integrates proven open-data APIs (`data.gov.in`, e-NAM, Agmarknet), reliable geospatial mapping (OpenStreetMap/OSRM), and standard scikit-learn / XGBoost regression libraries.
* **Operational Feasibility:** Streamlined interfaces with minimal required farmer inputs (crop, location, quantity, grade). Supports multilingual localization, simplified mobile layouts, and low-bandwidth resilience.
* **Economic Feasibility:** Built on open-source web technologies and public datasets, requiring minimal initial capital expenditure while directly increasing smallholder net income.

### 13.2 Viability Dimensions
* **Market Demand:** High necessity across Indian mandis where price asymmetry and opaque local cartels erode farmer margins. Directly serves individual farmers, FPOs, food processing companies, and bulk institutional buyers.
* **Financial Sustainability:** Hybrid operational model:
  1. Free tier for smallholder farmers providing core price intelligence.
  2. B2B enterprise tier charging listing and transaction processing fees to institutional buyers and processors.
  3. FPO analytics dashboard subscriptions.
* **Social & Strategic Viability:** Eliminates predatory middlemen exploitation, fosters collective farmer bargaining power through aggregation, and supports government procurement targets.

### 13.3 Strategic Benefits Summary
* **Higher Net Realization:** Enables farmers to evaluate price gains against fuel/transport costs across multiple destinations.
* **Reduced Distress Selling:** Storage-aware sell/wait intelligence allows producers of non-perishables (grains, pulses, oilseeds) to hold produce past harvest-time supply gluts.
* **Increased Trust:** Transparent confidence intervals and data-backed rationale rather than unverified price promises.
* **Streamlined B2B Procurement:** Verified digital lots reduce physical inspection times and blind-buy dispute rates for institutional buyers.

---

## 14. Research, Literature & Data Citations

### 14.1 Academic & Technical Research Papers
1. **Agricultural Price Prediction via Deep Learning & Time-Series Modeling:** [arXiv:1812.05173](https://arxiv.org/pdf/1812.05173)
2. **Food Policy & Market Information Systems in Developing Nations:** [Food Policy, Vol 81, 2018 (RePEc)](https://ideas.repec.org/a/eee/jfpoli/v81y2018icp106-121.html)
3. **Agricultural Supply Chain Optimization & Aggregation Models:** [European Journal of Operational Research, Vol 311, 2023](https://ideas.repec.org/a/eee/ejores/v311y2023i2p739-753.html)
4. **Machine Learning Applications in Agritech Price Discovery:** [Discover Agriculture, Springer 2025](https://link.springer.com/article/10.1007/s43621-025-01412-5)
5. **Decision Support Systems for Indian Agricultural Markets:** [Procedia Computer Science, ScienceDirect 2020](https://www.sciencedirect.com/science/article/pii/S1877050920310449)

### 14.2 Database Sources
* **Kaggle Agricultural Commodity Price Database:**  
  [https://www.kaggle.com/code/arvindkhoda/price-of-agricultural-commodities-data/input](https://www.kaggle.com/code/arvindkhoda/price-of-agricultural-commodities-data/input)
* **All Agriculture Related Datasets for India:**  
  [https://www.kaggle.com/datasets/thammuio/all-agriculture-related-datasets-for-india](https://www.kaggle.com/datasets/thammuio/all-agriculture-related-datasets-for-india)
* **National Public Data:** `data.gov.in` (Daily Mandi Price and Arrival Feeds) & Agmarknet.

### 14.3 Institutional Reports & Policy Frameworks
* **World Bank:** *A Roadmap for Building the Digital Future of Food and Agriculture*  
  [World Bank Feature (2021)](https://www.worldbank.org/en/news/feature/2021/03/16/a-roadmap-for-building-the-digital-future-of-food-and-agriculture)
* **Food and Agriculture Organization (FAO):** *e-Agriculture Framework & Good Practices*  
  [FAO e-Agriculture Node 14544](https://www.fao.org/e-agriculture/es/node/14544)

---

## 15. Antigravity Phased Development Roadmap (Phases 0–10)

> **Development Directive:** Do not build the entire system in one monolithic prompt. Implement incrementally phase by phase. Preserve existing architecture and verify each module before moving to the next.

| Phase | Phase Name | Core Deliverables | Verification Gate |
|---|---|---|---|
| **Phase 0** | **Foundation** | Initialize repository, folder structure, environment files, README, coding standards, Docker baseline. | Repo structure matches spec; dev environment boots cleanly. |
| **Phase 1** | **Frontend UI** | Build React + Vite UI with Tailwind CSS. Implement responsive layouts and mock data for all 9 key views. | All pages render with mock state, zero runtime JS errors. |
| **Phase 2** | **Backend Core** | Scaffold FastAPI app, Pydantic schemas, routing structure, configuration, and error handlers. | `/docs` Swagger UI accessible; health endpoints return 200 OK. |
| **Phase 3** | **PostgreSQL** | Define SQLAlchemy models, create migrations, establish foreign key relations, seed demo data. | CRUD operations on users, lots, and markets verified in PostgreSQL. |
| **Phase 4** | **Integration** | Replace frontend mock stores with live Axios calls to FastAPI endpoints; wire JWT auth tokens. | Login, dashboard, and lot creation execute end-to-end between UI and DB. |
| **Phase 5** | **Historical Data & ML** | Inspect raw Kaggle CSVs, clean nulls/duplicates, build chronological feature pipeline, train XGBoost model. | Model artifact serialized; out-of-sample MAE/RMSE logged and verified. |
| **Phase 6** | **Current API & Forecast** | Ingest `data.gov.in` live feeds, cache in DB with timestamps, expose `/api/forecast` using saved ML model. | API returns predicted price, upper/lower bounds, and confidence score. |
| **Phase 7** | **Decision & Net Realization** | Implement Net Realization formula, storage decay, and SELL NOW / WAIT / BEST BUYER decision service. | Engine outputs transparent numerical justification for recommendations. |
| **Phase 8** | **Market Linkage** | Implement buyer matching algorithm, reverse marketplace query, digital lot listing, and bulk lot aggregation. | Matching engine filters hard constraints and returns ranked buyer cards. |
| **Phase 9** | **Transactions** | Offer/counter-offer negotiation, deal state machine, delivery confirmation, payment statuses. | Transaction moves smoothly across lifecycle from offer to completion. |
| **Phase 10** | **Advanced QA & Demo Prep**| Storage/MSP benchmarks, dispute flow, expected-vs-actual variance report, security audit, demo seed data. | Full end-to-end 16-step demo executed without mock fallbacks. |

---

## 16. Antigravity Agent Prompt Sequence

When delegating tasks to autonomous developer agents, issue instructions using this precise 9-stage sequence:

* **Prompt 1: Foundation & UI Scaffold**  
  *"Build the complete React + Vite + Tailwind CSS frontend with modular components and mock data for Dashboard, Market Prices, Forecast, Buyers, Bulk Lots, Logistics, and Deals. Do not implement backend or ML yet."*
* **Prompt 2: FastAPI & PostgreSQL Core**  
  *"Create the FastAPI backend application with SQLAlchemy models and Pydantic schemas for users, lots, markets, buyers, and transactions. Implement database migrations and seed script."*
* **Prompt 3: Frontend-Backend Connectivity**  
  *"Connect React frontend to FastAPI via `api.js`. Wire authentication, dashboard metrics, lot creation, and market price browsing. Verify full CRUD flow."*
* **Prompt 4: Historical Data Inspection & ML Pipeline**  
  *"Inspect the actual raw agricultural CSV files. Build `preprocessing.py` and `features.py` with temporal lags and rolling averages. Train baseline and XGBoost models using chronological splits. Evaluate MAE and serialize model artifacts to `model_artifacts/`."*
* **Prompt 5: Live Ingestion & Forecast API**  
  *"Integrate the live market observation service with PostgreSQL caching. Build `predict.py` to ingest live features and generate bounded price forecasts. Expose via `GET /api/forecast`."*
* **Prompt 6: Net Realization & Decision Engine**  
  *"Implement `net_realization.py` and `decision_engine.py`. Combine live mandi prices, forecast delta, storage holding costs, and transport distance to output SELL NOW, WAIT, or BEST BUYER verdicts with full cost transparency."*
* **Prompt 7: Buyer Matching, Bulk Aggregation & Logistics**  
  *"Build `buyer_matching.py` with hard filters and multi-factor scoring. Implement bulk aggregation linking child lots to master lots. Wire OSRM route distance calculations in `logistics_service.py`."*
* **Prompt 8: Transaction State Machine, Offers & Grievances**  
  *"Implement digital negotiation workflows (offer, counter, accept), the complete transaction lifecycle state machine, payment status tracking, buyer reliability calculations, and grievance management."*
* **Prompt 9: End-to-End QA, Security & Verification**  
  *"Perform a complete QA audit. Verify expected-vs-actual variance tracking, run security checks (JWT expiry, parameter validation, environment secret isolation), seed comprehensive demo data, and verify the 16-step demo scenario."*

---

## 17. Complete 16-Step Demonstration Scenario

1. **Farmer Login:** Farmer logs into KrishiDisha web dashboard via mobile or desktop.
2. **Lot Input:** Farmer selects crop (e.g., Wheat), enters quantity (100 Quintals), village location, Grade A, and confirms on-farm storage availability.
3. **Live Market Discovery:** System fetches latest nearby mandi prices (e.g., Mandi A: ₹2,520, Mandi B: ₹2,580, Mandi C: ₹2,490).
4. **Historical Trend Analysis:** Dashboard displays 30-day historical price movement and local arrival volumes.
5. **AI Price Forecasting:** ML engine predicts 7-day future price range (₹2,640 – ₹2,710/Q) with an upward trend indicator (84% confidence).
6. **Buyer Matching:** System scans private millers and institutional buyers; identifies 3 qualified buyers with matching quality criteria.
7. **Bulk Opportunity Check:** System alerts that two neighbouring farmers have 70Q and 80Q of compatible Wheat; offers bulk aggregation for volume freight discount.
8. **Logistics Cost Computation:** OSRM calculates road distances; logistics engine estimates transport cost for each buyer and mandi destination.
9. **Net Realization Ranking:** System computes Net Realization for all channels:
   * Mandi A: Gross ₹2,52,000 − ₹800 transport = ₹2,51,200 net.
   * Mandi B: Gross ₹2,58,000 − ₹3,500 transport = ₹2,54,500 net.
   * Buyer X: Gross ₹2,65,000 − ₹2,200 transport = ₹2,62,800 net.
10. **Action Recommendation:** Decision engine advises: **WAIT 4 DAYS OR ACCEPT BUYER X** (Net gain outweighs storage cost of ₹350).
11. **Digital Lot Creation:** Farmer clicks to publish Lot #WD-104 with verified specs.
12. **Offer Negotiation:** Buyer X submits an offer at ₹2,630/Q. Farmer sends counter-offer at ₹2,650/Q; Buyer X accepts.
13. **Transaction Contract:** System locks deal terms and initializes Transaction #TX-9082.
14. **Dispatch & Delivery:** Produce is transported to Buyer X's receiving warehouse; physical quantity (99.6Q) and moisture (11.8%) are confirmed.
15. **Payment Settlement:** Buyer confirms payment of ₹2,63,940; payment status updates to `PAID`.
16. **Actual Net & Variance Reporting:** Farmer receives final settlement summary showing expected vs. actual net realization (₹2,61,740 actual vs. ₹2,62,800 projected; variance: −₹1,060 due to 0.4Q weight variation). Transaction data feeds back into the model pipeline.

---

## 18. Critical Implementation Rules & Checklist

### 18.1 Critical Implementation Rules
* **No Pinpoint Predictions:** Never output a single guaranteed future price; always output a **range + trend direction + confidence score**.
* **Net Realization is King:** The recommendation engine must rank options by **Net Realization**, never by gross headline price alone.
* **Separation of Concerns:** Forecasting and decision-making are distinct modules. Machine learning predicts price probability; the decision engine applies economic constraints and business rules.
* **Prevent Data Leakage:** Never use random train/test splits on time-series datasets. Only use strict chronological splits.
* **Controlled Retraining:** Model inference must use pre-compiled saved model artifacts. User requests must never trigger live ad-hoc retraining.
* **Honest Metrics:** Never fabricate ML accuracy figures or transaction volumes. Only report empirically measured values from the validation set.
* **No Unverified Claims:** Do not claim government-certified buyer status unless an official verification API is integrated. Do not claim guaranteed MSP procurement if eligibility/center criteria are unmet.
* **Secure Architecture:** Store all database credentials and API keys in environment variables; never hardcode secrets or expose backend credentials in client-side bundles.

### 18.2 Team Execution Checklist
* [ ] 1. Repository initialized with frontend, backend, and ml directories.
* [ ] 2. React UI functional with responsive layout and clean visual hierarchy.
* [ ] 3. FastAPI application running with OpenAPI documentation at `/docs`.
* [ ] 4. PostgreSQL schema tables, relationships, and foreign keys created.
* [ ] 5. Frontend connected to backend via centralized `api.js`.
* [ ] 6. Historical agricultural price CSVs inspected, cleaned, and normalized.
* [ ] 7. Feature engineering pipeline (`features.py`) implemented and shared.
* [ ] 8. Baseline models (Moving Average, Ridge) and XGBoost model trained.
* [ ] 9. Chronological out-of-sample test evaluation completed and logged.
* [ ] 10. Best model serialized and versioned in `backend/ml/model_artifacts/`.
* [ ] 11. `data.gov.in` / Agmarknet live price integration running with database caching.
* [ ] 12. `/api/forecast` endpoint operational with live feature generation.
* [ ] 13. Net Realization Engine calculating transport, storage, and handling costs.
* [ ] 14. SELL NOW / WAIT / BEST BUYER decision engine returning structured rationale.
* [ ] 15. Multi-factor buyer matching algorithm operational with hard filters.
* [ ] 16. Digital lot creation, listing, and inspection functioning.
* [ ] 17. Bulk lot aggregation operational with farmer share traceability.
* [ ] 18. OSRM route distance and logistics freight estimation working.
* [ ] 19. Digital offer, counter-offer, and acceptance workflow verified.
* [ ] 20. Complete transaction lifecycle state machine operational.
* [ ] 21. Payment tracking system (`PENDING`, `PARTIAL`, `PAID`, `DISPUTED`) implemented.
* [ ] 22. Buyer reliability metric calculation functioning.
* [ ] 23. Storage facility comparison and MSP procurement benchmarks integrated.
* [ ] 24. Grievance and dispute logging workflow operational.
* [ ] 25. Expected vs. Actual net realization and variance tracking functioning.
* [ ] 26. End-to-end 16-step user journey demo verified without mock fallbacks.
* [ ] 27. SIH presentation deck updated with actual measured model performance metrics.
