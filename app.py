# app.py
from flask import Flask, render_template, request, jsonify
import pandas as pd
import joblib
import os

app = Flask(__name__)
MODEL_PATH = 'model.pkl'
MONTHLY_CSV = 'data/monthly_usage_sample.csv'

# load model if exists (used only for example — we primarily use formula)
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    if os.path.exists(MONTHLY_CSV):
        df = pd.read_csv(MONTHLY_CSV)
        # Return last 12 months
        df = df.tail(12)
        data = df.to_dict(orient='records')
        return jsonify({'status':'ok','data':data})
    return jsonify({'status':'error','message':'monthly CSV missing'})

@app.route('/predict', methods=['POST'])
def predict():
    """
    expected JSON:
    {
      "existing_kwh": float,   # current monthly kWh (sum of zones or user input)
      "rate": float,           # ₹/kWh
      "appliances": [          # list optional; we accept 0 or 1 appliance for simplicity
         {"name":"Heater","power_w":2000,"hours_per_day":2,"days":30}
      ]
    }
    """
    req = request.get_json(force=True)
    try:
        existing_kwh = float(req.get('existing_kwh', 0))
        rate = float(req.get('rate', 8.0))
        appliances = req.get('appliances', [])
        days_in_month = int(req.get('days_in_month', 30))
        extra_kwh = 0.0
        appliance_impacts = []
        for a in appliances:
            p_w = float(a.get('power_w',0))
            hours = float(a.get('hours_per_day',0))
            days = int(a.get('days', days_in_month))
            kwh = (p_w * hours * days) / 1000.0
            cost = kwh * rate
            extra_kwh += kwh
            appliance_impacts.append({'name': a.get('name','appliance'), 'kwh':round(kwh,3), 'cost': round(cost,2)})
        predicted_total_kwh = existing_kwh + extra_kwh
        predicted_bill = predicted_total_kwh * rate
        return jsonify({
            'status':'ok',
            'predicted_total_kwh': round(predicted_total_kwh,3),
            'predicted_bill': round(predicted_bill,2),
            'extra_kwh': round(extra_kwh,3),
            'extra_cost': round(extra_kwh*rate,2),
            'appliance_impacts': appliance_impacts
        })
    except Exception as e:
        return jsonify({'status':'error','message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
