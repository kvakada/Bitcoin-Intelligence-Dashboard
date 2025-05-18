from flask import Flask, render_template, jsonify
from ingestion.fetch import fetch_bitcoin
from processing.preprocess import load_all_btc_data
from processing.analysis import (
    decompose_price,
    compute_moving_avg,
    detect_anomalies,
    add_technical_indicators
)
from forecasting.prophet_model import run_prophet
from visualization.interactive import (
    plot_btc,
    plot_ma,
    plot_anomalies,
    plot_ma_comparison,
    plot_ema,
    plot_macd,
    plot_returns,
    plot_cumulative_returns,
    plot_price_change,
    plot_volatility,
    plot_forecast_interactive
)

app = Flask(__name__)

@app.route('/')
def dashboard():
    try:
        df = load_all_btc_data()
        df = compute_moving_avg(df)
        df = detect_anomalies(df)
        df = add_technical_indicators(df)

        print("Columns in dataframe:", df.columns.tolist())

        required_cols = [
            'MA_7', 'MA_30', 'EMA_12', 'EMA_26',
            'MACD', 'Signal', 'Returns', 'Cumulative_Return',
            'Price_Change', 'Volatility'
        ]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column in df: {col}")

        # Forecast deferred to a separate route to avoid Render timeout
        forecast_table = "<div style='color:orange;'>Forecast loading separately...</div>"
        forecast_plot = "<div style='color:orange;'>Loading...</div>"

        btc_plot = try_plot(plot_btc, df, "BTC")
        ma_plot = try_plot(plot_ma, df, "MA")
        anomaly_plot = try_plot(plot_anomalies, df, "Anomaly")
        ma_comparison_plot = try_plot(plot_ma_comparison, df, "MA Comparison")
        ema_plot = try_plot(plot_ema, df, "EMA")
        macd_plot = try_plot(plot_macd, df, "MACD")
        returns_plot = try_plot(plot_returns, df, "Returns")
        cumulative_plot = try_plot(plot_cumulative_returns, df, "Cumulative Returns")
        price_change_plot = try_plot(plot_price_change, df, "Price Change")
        volatility_plot = try_plot(plot_volatility, df, "Volatility")

        return render_template("index.html",
                               btc_plot=btc_plot,
                               ma_plot=ma_plot,
                               anomaly_plot=anomaly_plot,
                               ma_comparison_plot=ma_comparison_plot,
                               ema_plot=ema_plot,
                               macd_plot=macd_plot,
                               returns_plot=returns_plot,
                               cumulative_plot=cumulative_plot,
                               price_change_plot=price_change_plot,
                               volatility_plot=volatility_plot,
                               forecast_table=forecast_table,
                               forecast_plot=forecast_plot)
    except Exception as e:
        print("Dashboard error:", e)
        return render_template("index.html", btc_plot=None, error=str(e))


@app.route('/api/forecast')
def api_forecast():
    try:
        df = load_all_btc_data()
        df = compute_moving_avg(df)
        forecast = run_prophet(df)

        forecast_plot = plot_forecast_interactive(forecast)
        forecast_table = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(10).round(2).to_html(index=False)

        return jsonify({
            "forecast_plot": forecast_plot,
            "forecast_table": forecast_table
        })
    except Exception as e:
        print("Forecast API error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/refresh')
def refresh():
    try:
        fetch_bitcoin()
        return jsonify({"status": "updated"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Reusable helper to catch plot errors
def try_plot(plot_func, df, label):
    try:
        return plot_func(df)
    except Exception as e:
        print(f"{label} plot error:", e)
        return f"<div style='color:red;'>{label} Plot Error: {e}</div>"
