# Telecom Behavior Analyzer

A **Streamlit-based analytics application** that analyzes telecom customer behavior, clusters customers based on usage patterns, predicts future usage, and recommends optimal plans with churn-awareness.

This project is designed to demonstrate **time-series data mining**, **DTW-based clustering**, **usage prediction**, and **rule-based + data-driven recommendations** in a single interactive dashboard.

Deployed: https://telecom-plan-analytics.streamlit.app/

---

## What the Application Does

The app is divided into several analytical components:

### Data Preprocessing
- Converts raw monthly customer records into **time-series per customer**
- Normalizes usage metrics using z-score normalization
- Prepares data for clustering, prediction, and recommendation

### Customer Clustering (DTW Time-Series Clustering)
- Groups customers based on **behavioral similarity over time**
- Uses **Dynamic Time Warping (DTW)** to compare usage trends, not just raw values
- Each cluster represents a distinct usage profile (e.g. stable users, growing users, heavy users)

### Cluster Insights Dashboard
- Visualizes **average behavior per cluster**
- Shows trends across multiple years (data, voice, roaming, billing)
- Helps understand how different customer segments behave over time

### Usage Prediction System
- Predicts future usage based on historical data (2022 + 2023 → 2024)
- Two prediction modes:
  - **Cluster-only prediction** (based on the cluster’s own history)
  - **Cross-cluster-informed prediction** (borrowing trends from similar clusters)
- Uses a combination of:
  - Linear trend
  - Seasonal patterns (sin / cos)

### Plan Recommendation Engine
- Recommends the most suitable telecom plan per customer
- Based on:
  - Expected future usage
  - Plan limits and costs
  - Historical billing behavior

### Churn-Aware Recommendations
- Detects **unexpected bill increases**
- Flags plans that may cause customer dissatisfaction
- Suggests safer alternatives to reduce churn risk

### Recommendation Evaluation
- Compares **before vs after** scenarios
- Measures potential cost savings and stability improvements
- Helps validate whether recommendations actually improve outcomes

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/dionahalilaj/telecom.git
cd telecom_app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## How to Run the Application

From the project root directory:

```bash
python -m streamlit run app.py
```

Then open your browser at:
```
http://localhost:8501

