import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import logging
import os
import sys

# Import data fetching utilities
from database_utils import fetch_store_names, fetch_customer_stats, fetch_monthly_revenue, fetch_top_customers, fetch_order_trends, fetch_category_order_trends, fetch_order_totals

# Configure logging to screen and file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "store_analysis.log")),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize the Dash app
app = dash.Dash(__name__)

app.layout = html.Div(style={'backgroundColor': '#111111', 'minHeight': '100vh'}, children=[
    # Fixed Header Section: Contains Title, Filters, and Tabs
    html.Div(style={
        'position': 'fixed',
        'top': '0',
        'left': '0',
        'width': '100%',
        'zIndex': '1000',
        'backgroundColor': '#111111',
        'padding': '20px 20px 0 20px',
        'borderBottom': '1px solid #333333'
    }, children=[
        html.H1(children='Store Analysis Dashboard', style={'textAlign': 'center', 'color': '#7FDBFF', 'fontFamily': 'Arial', 'marginTop': '0'}),
        
        html.Div([
            html.Div([
                html.Label("Select Store:", style={'color': '#7FDBFF', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='store-id-dropdown',
                    options=[{'label': 'All Stores', 'value': 'All'}] + [{'label': str(name), 'value': name} for name in fetch_store_names()],
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
            ]),

            html.Div([
                html.Label("Select Account Type:", style={'color': '#7FDBFF', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='account-type-dropdown',
                    options=[
                        {'label': 'All Accounts', 'value': 'All'},
                        {'label': 'Commercial', 'value': 'Commercial'},
                        {'label': 'Retail', 'value': 'Retail'}
                    ],
                    value='All',
                    style={'width': '200px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                )
            ], style={'marginLeft': '40px'})
        ], style={
            'display': 'flex', 
            'justifyContent': 'center', 
            'alignItems': 'center', 
            'marginBottom': '20px'
        }),

        dcc.Tabs(id="tabs-navigation", value='tab-store', children=[
            dcc.Tab(label='Store Analysis', value='tab-store', 
                    style={'backgroundColor': '#222222', 'color': '#7FDBFF', 'border': '1px solid #333333'},
                    selected_style={'backgroundColor': '#111111', 'color': 'white', 'borderTop': '2px solid #7FDBFF'}),
            dcc.Tab(label='Customer Analysis', value='tab-customer',
                    style={'backgroundColor': '#222222', 'color': '#7FDBFF', 'border': '1px solid #333333'},
                    selected_style={'backgroundColor': '#111111', 'color': 'white', 'borderTop': '2px solid #7FDBFF'}),
        ], style={'marginBottom': '0px'}),
    ]),

    # Scrollable Content Section
    html.Div(id='tabs-content', style={'padding': '280px 20px 20px 20px'})
])

@app.callback(
    Output('tabs-content', 'children'),
    [Input('tabs-navigation', 'value'),
     Input('store-id-dropdown', 'value'), # Now passing Store Name
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value')]
)
def render_tab_content(active_tab, selected_store_name, start_date, end_date, account_filter):
    if active_tab == 'tab-store':
        return update_store_analysis(selected_store_name, start_date, end_date, account_filter)
    else:
        return update_customer_analysis(selected_store_name, account_filter)

def update_store_analysis(selected_store_name, start_date, end_date, account_filter):
    df_revenue = fetch_monthly_revenue(selected_store_name, start_date, end_date, account_filter)
    df_trends = fetch_order_trends(selected_store_name, start_date, end_date, account_filter)
    df_cat_trends = fetch_category_order_trends(selected_store_name, start_date, end_date, account_filter)
    df_totals = fetch_order_totals(selected_store_name, start_date, end_date, account_filter)
    
    title = f'Monthly Revenue Overview - Store: {selected_store_name}'
    
    if not df_revenue.empty:
        # Group data for the line chart (total pieces per month regardless of account type)
        df_line = df_revenue.groupby('month_year')['total_pieces'].sum().reset_index()

        fig = px.bar(
            df_revenue,
            x='month_year',
            y='total_revenue',
            color='account_type',
            title=title,
            labels={'month_year': 'Month (YYYY-MM)', 'total_revenue': 'Total Revenue ($)', 'account_type': 'Account Type'},
            template='plotly_dark'
        )

        # Add the Line Chart for Pieces on a secondary Y-axis
        fig.add_trace(
            go.Scatter(
                x=df_line['month_year'],
                y=df_line['total_pieces'],
                name='Total Pieces',
                mode='lines+markers',
                line=dict(color='#FFD700', width=3),
                yaxis='y2'
            )
        )

        fig.update_layout(
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font_color='#7FDBFF',
            yaxis2=dict(
                title='Total Pieces',
                overlaying='y',
                side='right',
                showgrid=False,
                color='#FFD700'
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig = px.scatter(title="No data available for the selected criteria.", template='plotly_dark')
        fig.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')
    

    if not df_trends.empty:
        fig_trends = go.Figure()
        fig_trends.add_trace(go.Scatter(
            x=df_trends['month_year'], y=df_trends['median_invoice'],
            name='Median Invoice', mode='lines+markers', line=dict(color='#00CC96', width=3)
        ))
        fig_trends.add_trace(go.Scatter(
            x=df_trends['month_year'], y=df_trends['order_count'],
            name='Order Count', mode='lines+markers', line=dict(color='#7FDBFF', width=3),
            yaxis='y2'
        ))
        fig_trends.update_layout(
            title='Monthly Order Trends: Median Value vs Volume',
            template='plotly_dark',
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            yaxis=dict(title='Median Invoice ($)'),
            yaxis2=dict(title='Order Count', overlaying='y', side='right', showgrid=False, color='#7FDBFF'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig_trends = px.scatter(title="No trend data available for the selected criteria.", template='plotly_dark')
        fig_trends.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

    # Order count by category bar chart
    category_order = [
        '1) One Time', '2) Second', '3) Third', '4) Comfortable', 
        '5) Regular', '6) Super Regular', '7) Big Dawgs'
    ]

    if not df_cat_trends.empty:
        fig_cat = px.bar(
            df_cat_trends, x='month_year', y='order_count', color='customer_category',
            title='Order Volume by Customer Category',
            labels={'month_year': 'Month', 'order_count': 'Orders', 'customer_category': 'Category'},
            category_orders={'customer_category': category_order},
            template='plotly_dark'
        )
        fig_cat.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig_cat = px.scatter(title="No category trend data available.", template='plotly_dark')
        fig_cat.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

    # Order Totals Histogram
    if not df_totals.empty:
        # Clip values at 200 to create a single overflow bin for all orders > $200
        df_hist_data = df_totals.copy()
        df_hist_data['Total'] = df_hist_data['Total'].clip(upper=200)

        fig_hist = px.histogram(
            df_hist_data, x='Total',
            title='Distribution of Order Totals',
            labels={'Total': 'Order Total ($)'},
            template='plotly_dark',
            nbins=40 # This creates consistent $5 bins for the 0-200 range
        )
        fig_hist.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            bargap=0.1,
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 50, 100, 150, 200],
                ticktext=['$0', '$50', '$100', '$150', '$200+']
            )
        )
        fig_hist.update_traces(marker_color='#00CC96')
    else:
        fig_hist = px.scatter(title="No order total data available.", template='plotly_dark')
        fig_hist.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')
    
    return html.Div([
        dcc.Graph(id='revenue-bar-chart', figure=fig),
        html.Div([
            html.Div(dcc.Graph(id='order-trends-chart', figure=fig_trends), style={'width': '50%'}),
            html.Div(dcc.Graph(id='category-trends-chart', figure=fig_cat), style={'width': '50%'})
        ], style={'display': 'flex'}),
        html.Div([
            dcc.Graph(id='order-totals-histogram', figure=fig_hist)
        ])
    ])

def update_customer_analysis(selected_store, account_filter):
    df_cust = fetch_customer_stats(selected_store, account_filter)
    df_top = fetch_top_customers(selected_store, account_filter)
    
    if df_cust.empty and df_top.empty:
        return html.Div("No customer data available.", style={'color': '#7FDBFF', 'textAlign': 'center'})

    # Define a consistent order for categories to ensure matching colors across plots
    category_order = [
        '1) One Time', '2) Second', '3) Third', '4) Comfortable', 
        '5) Regular', '6) Super Regular', '7) Big Dawgs'
    ]

    fig_count = px.pie(
        df_cust, values='customer_count', names='customer_category',
        title='Customer Distribution by Category',
        template='plotly_dark',
        hole=0.4,
        category_orders={'customer_category': category_order}
    )
    
    fig_spend = px.pie(
        df_cust, values='total_spend', names='customer_category',
        title='Total Spend by Category',
        template='plotly_dark',
        hole=0.4,
        category_orders={'customer_category': category_order}
    )

    # Hover information setup for consistent tooltips across bar and line traces
    custom_hover_cols = ['customer_category', 'order_count', 'discount', 'recency', 'median_days_between_orders']
    common_hover = (
        "Category: %{customdata[0]}<br>"
        "Order Count: %{customdata[1]}<br>"
        "Discount: %{customdata[2]}%<br>"
        "Last Order: %{customdata[3]:.0f} days ago<br>"
        "Median Interval: %{customdata[4]:.1f} days"
        "<extra></extra>"
    )

    # Combined Bar and Line chart for Top Customers
    # Use Plotly Express for the Bar portion to handle categorical coloring automatically
    fig_top = px.bar(
        df_top,
        x='Name',
        y='total_spend',
        title='Top Customers: Lifetime Value vs Median Order Amount',
        labels={'total_spend': 'Total Spending'},
        custom_data=custom_hover_cols,
        template='plotly_dark'
    )

    # Apply the custom hover template to the bar traces generated by Plotly Express
    fig_top.update_traces(
        marker_color='#00CC96',
        hovertemplate="Total Spend: $%{y:,.2f}<br>" + common_hover,
        selector=dict(type='bar')
    )

    fig_top.add_trace(go.Scatter(
        x=df_top['Name'], 
        y=df_top['median_spend'], 
        name='Median Spend',
        line=dict(color='#7FDBFF', width=3),
        mode='lines+markers',
        customdata=df_top[custom_hover_cols],
        hovertemplate="Median Spend: $%{y:,.2f}<br>" + common_hover
    ))
    
    fig_top.update_layout(hovermode='x unified')

    for fig in [fig_count, fig_spend, fig_top]:
        fig.update_layout(
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font_color='#7FDBFF'
        )

    return (html.Div([
        html.Div([
            dcc.Graph(id='customer-count-pie', figure=fig_count)
        ], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(id='customer-spend-pie', figure=fig_spend)
        ], style={'width': '50%', 'display': 'inline-block'})
    ], style={'display': 'flex'}),
    html.Div([
        dcc.Graph(id='top-customer-bar-line', figure=fig_top)
    ]),)

if __name__ == '__main__':
    app.run(debug=True)