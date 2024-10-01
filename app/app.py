from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import json
from model import get_historical_and_future_data, base
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    to_date = request.form['to_date']
    # Convert the date string to the format expected by your model
    to_date = datetime.strptime(to_date, "%d/%m/%Y").strftime("%d/%m/%Y")
    
    historical_prices, historical_dates, future_prices, future_dates = get_historical_and_future_data(to_date)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(x=historical_dates, y=historical_prices, name='Historical Data', line=dict(color='blue'))
    )

    fig.add_trace(
        go.Scatter(x=future_dates, y=future_prices, name='Future Prediction', line=dict(color='red'))
    )

    fig.update_layout(
        title='Ethereum Price Prediction including Future Forecast',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        legend_title='Data',
        hovermode="x unified"
    )

    graphJSON = json.dumps(fig, cls=PlotlyJSONEncoder)

    return jsonify({
        'plot': graphJSON,
        'last_price': float(historical_prices[-1]),
        'predicted_price': float(future_prices[-1])
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)