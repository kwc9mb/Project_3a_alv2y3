from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
import pandas as pd
import pygal
import os
import secrets
from StockDataAnalyzer import get_data, filter_by_date_range, get_stock_symbols

app = Flask(__name__, static_folder='static')
# Securely set the secret key
if app.config.get("ENV") == "development":
   app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
else:
   app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'A default secret key')

app.config['SESSION_TYPE'] = 'filesystem'

class StockForm(FlaskForm):
   symbol = SelectField('Stock Symbol', choices=[])
   time_series = SelectField('Time Series', choices=[
      ('1', 'Intraday'), 
      ('2', 'Daily'), 
      ('3', 'Weekly'), 
      ('4', 'Monthly')
   ])
   start_date = DateField('Start Date', format='%Y-%m-%d')
   end_date = DateField('End Date', format='%Y-%m-%d')
   chart_type = SelectField('Chart Type', choices=[
      ('line', 'Line'), 
      ('bar', 'Bar')
   ])
   submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def home():
   form = StockForm()
   form.symbol.choices = [(symbol, symbol) for symbol in get_stock_symbols('stocks.csv')]

   if form.validate_on_submit():
      symbol = form.symbol.data
      time_series = form.time_series.data
      start_date = form.start_date.data
      end_date = form.end_date.data
      chart_type = form.chart_type.data

      # Check if start date is after end date
      if start_date and end_date and start_date > end_date:
         flash('Start date must be before end date.')
         return redirect(url_for('home'))

      start_date_str = start_date.strftime('%Y-%m-%d') if start_date else None
      end_date_str = end_date.strftime('%Y-%m-%d') if end_date else None

      data = get_data(symbol, '67ZV81HC5LKYSLBY', time_series)
      if data is None:
         flash(f'API call error for {symbol} with time series {time_series}.')
         return redirect(url_for('home'))

      if data.empty:
         flash(f'No data available for {symbol} with time series {time_series}.')
         return redirect(url_for('home'))

      filtered_data = filter_by_date_range(data, start_date_str, end_date_str)
      chart_file_name = f"{symbol}_{time_series}_{chart_type}.svg"

      # Create chart based on selected chart type
      if chart_type == 'line':
         chart = pygal.Line(title=f"Stock Data for {symbol}", x_label_rotation=20)
      elif chart_type == 'bar':
         chart = pygal.Bar(title=f"Stock Data for {symbol}", x_label_rotation=20)
      else:
         flash('Invalid chart type selected.')
         return redirect(url_for('home'))

      chart.x_labels = map(lambda d: d.strftime('%Y-%m-%d'), filtered_data.index.date)
      chart.y_title = "Price (USD)"
      chart.add('Open', filtered_data['1. open'].tolist())
      chart.add('High', filtered_data['2. high'].tolist())
      chart.add('Low', filtered_data['3. low'].tolist())
      chart.add('Close', filtered_data['4. close'].tolist())

      chart.render_to_file(os.path.join('static', chart_file_name))
      session['chart_file_name'] = chart_file_name
      return redirect(url_for('results'))

   return render_template('home.html', form=form)


@app.route('/results')
def results():
   if 'chart_file_name' in session:
      chart_file_name = session['chart_file_name']
      return render_template('results.html', chart=chart_file_name)
   else:
      flash('No data to display. Please make a new selection.')
      return redirect(url_for('home'))

if __name__ == "__main__":
   app.run(debug=True)
