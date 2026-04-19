import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from datetime import datetime
import pandas as pd

# Import data fetching utilities
from database_utils import fetch_store_ids, fetch_customer_stats, fetch_monthly_revenue

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#111111', 'minHeight': '100vh', 'padding': '20px'}, children=[
    html.H1(children='Store Analysis Dashboard', style={'textAlign': 'center', 'color': '#7FDBFF', 'fontFamily': 'Arial'}),
    html.Div(children='Performance metrics and sales trends.', style={'textAlign': 'center', 'color': '#7FDBFF', 'marginBottom': '20px'}),
    
    html.Div([
        html.Div([
            html.Label("Select Store ID:", style={'color': '#7FDBFF', 'marginRight': '10px'}),
            dcc.Dropdown(
                id='store-id-dropdown',
                options=[{'label': 'All Stores', 'value': 'All'}] + [{'label': f'Store {i}', 'value': i} for i in fetch_store_ids()],
                value='All',
                style={'width': '300px', 'display': 'inline-block', 'verticalAlign': 'middle'}
            )
        ], style={'marginRight': '40px'}),

        html.Div([
            html.Label("Select Date Range:", style={'color': '#7FDBFF', 'marginRight': '10px'}),
            dcc.DatePickerRange(
                id='date-range-picker',
                start_date_placeholder_text="Start Date",
                end_date_placeholder_text="End Date",
                style={
                    'color': '#7FDBFF', 'backgroundColor': '#222222', 'border': '1px solid #333333',
                    'borderRadius': '5px', 'padding': '5px', 'display': 'inline-block', 'verticalAlign': 'middle'
                }
            )
        ])
    ], style={
        'display': 'flex', 
        'justifyContent': 'center', 
        'alignItems': 'center', 
        'marginBottom': '40px'
    }),

    dcc.Tabs(id="tabs-navigation", value='tab-store', children=[
        dcc.Tab(label='Store Analysis', value='tab-store', 
                style={'backgroundColor': '#222222', 'color': '#7FDBFF', 'border': '1px solid #333333'},
                selected_style={'backgroundColor': '#111111', 'color': 'white', 'borderTop': '2px solid #7FDBFF'}),
        dcc.Tab(label='Customer Analysis', value='tab-customer',
                style={'backgroundColor': '#222222', 'color': '#7FDBFF', 'border': '1px solid #333333'},
                selected_style={'backgroundColor': '#111111', 'color': 'white', 'borderTop': '2px solid #7FDBFF'}),
    ], style={'marginBottom': '20px'}),

    html.Div(id='tabs-content')
])

@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs-navigation', 'value'),
     Input('store-id-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date')]
)
def render_tab_content(active_tab, selected_store, start_date, end_date):
    if active_tab == 'tab-store':
        return update_store_analysis(selected_store, start_date, end_date)
    else:
        return update_customer_analysis(selected_store)

def update_store_analysis(selected_store, start_date, end_date):
    df_revenue = fetch_monthly_revenue(selected_store, start_date, end_date)
    
    title = f'Monthly Revenue Overview - Store: {selected_store}'
    
    if not df_revenue.empty:
        fig = px.bar(
            df_revenue,
            x='month_year',
            y='total_revenue',
            color='account_type',
            title=title,
            labels={'month_year': 'Month (YYYY-MM)', 'total_revenue': 'Total Revenue ($)', 'account_type': 'Account Type'},
            template='plotly_dark'
        )
        fig.update_layout(
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font_color='#7FDBFF'
        )
    else:
        fig = px.scatter(title="No data available for the selected criteria.", template='plotly_dark')
        fig.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')
    
    return dcc.Graph(id='revenue-bar-chart', figure=fig)

def update_customer_analysis(selected_store):
    df_cust = fetch_customer_stats(selected_store)
    
    if df_cust.empty:
        return html.Div("No customer data available.", style={'color': '#7FDBFF', 'textAlign': 'center'})

    fig_count = px.pie(
        df_cust, values='customer_count', names='customer_category',
        title='Customer Distribution by Category',
        template='plotly_dark',
        hole=0.4
    )
    
    fig_spend = px.pie(
        df_cust, values='aggregate_spend', names='customer_category',
        title='Total Spend by Category',
        template='plotly_dark',
        hole=0.4
    )

    for fig in [fig_count, fig_spend]:
        fig.update_layout(
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font_color='#7FDBFF'
        )

    return html.Div([
        html.Div([
            dcc.Graph(id='customer-count-pie', figure=fig_count)
        ], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(id='customer-spend-pie', figure=fig_spend)
        ], style={'width': '50%', 'display': 'inline-block'})
    ], style={'display': 'flex'})

if __name__ == '__main__':
    app.run(debug=True)