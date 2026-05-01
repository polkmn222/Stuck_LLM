import pandas as pd
import statsmodels.api as sm
from typing import Dict, Any

def analyze_price_trend(prices: list[float]) -> Dict[str, Any]:
    """
    Analyzes the price trend using OLS regression from statsmodels.
    Returns the slope (trend), intercept, and p-value.
    """
    if len(prices) < 2:
        return {"slope": 0.0, "p_value": 1.0, "is_significant": False}

    df = pd.DataFrame({"price": prices})
    df["time"] = range(len(prices))
    
    X = sm.add_constant(df["time"])
    y = df["price"]
    
    model = sm.OLS(y, X)
    results = model.fit()
    
    slope = results.params["time"]
    p_value = results.pvalues["time"]
    
    return {
        "slope": float(slope),
        "p_value": float(p_value),
        "is_significant": bool(p_value < 0.05),
        "r_squared": float(results.rsquared)
    }
