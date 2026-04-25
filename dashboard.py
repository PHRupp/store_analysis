import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd
import logging
import os
import sys
import argparse

# Import data fetching utilities
import database_utils
from database_utils import (
    fetch_store_names, 
    fetch_customer_stats, 
    fetch_monthly_revenue, 
    fetch_top_customers, 
    fetch_order_trends, 
    fetch_category_order_trends, 
    fetch_order_totals, 
    fetch_overdue_customers, 
    fetch_daytime_data, 
    fetch_collection_data,
    fetch_new_customers_trend,
    fetch_last_order_trend,
)

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

# Parse command line arguments for database location
parser = argparse.ArgumentParser(description="Store Analysis Dashboard")
parser.add_argument("--database", default=database_utils.DB_PATH, help="Path to the SQLite database file")
args, _ = parser.parse_known_args()

# Update the database path in the utility module
database_utils.DB_PATH = os.path.abspath(args.database)
database_utils.DB_NAME = os.path.basename(args.database)
logger.info(f"Using database at: {database_utils.DB_PATH}")

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Unified category configuration to ensure matching colors across all charts
CATEGORY_ORDER = [
    '1 One Time', '2-3 Testing', '4-9 Comfortable', '10-19 Regular', '20-49 Super Regular', '50+ Big Dawgs'
]
CATEGORY_COLORS = {
    cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
    for i, cat in enumerate(CATEGORY_ORDER)
}

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
            ], style={'marginLeft': '40px'}),

            # Day of Week Filter (Only shown for Daytime Tab)
            html.Div(id='day-filter-container', style={'display': 'none', 'marginLeft': '40px'}, children=[
                html.Label("Filter by Day:", style={'color': '#7FDBFF', 'marginRight': '10px'}),
                dcc.Dropdown(
                    id='daytime-day-filter',
                    options=[
                        {'label': 'All Days', 'value': 'All'},
                        {'label': 'Sunday', 'value': '0'},
                        {'label': 'Monday', 'value': '1'},
                        {'label': 'Tuesday', 'value': '2'},
                        {'label': 'Wednesday', 'value': '3'},
                        {'label': 'Thursday', 'value': '4'},
                        {'label': 'Friday', 'value': '5'},
                        {'label': 'Saturday', 'value': '6'},
                    ],
                    value='All',
                    style={'width': '180px', 'display': 'inline-block', 'verticalAlign': 'middle'}
                )
            ])
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
            dcc.Tab(label='DayTime Analysis', value='tab-daytime',
                    style={'backgroundColor': '#222222', 'color': '#7FDBFF', 'border': '1px solid #333333'},
                    selected_style={'backgroundColor': '#111111', 'color': 'white', 'borderTop': '2px solid #7FDBFF'}),
        ], style={'marginBottom': '0px'}),
    ]),

    # Scrollable Content Sections
    html.Div(style={'padding': '280px 20px 20px 20px'}, children=[
        html.Div(id='tabs-content'),
        # Permanently in layout to avoid callback errors, visibility toggled by tab
        html.Div(id='daytime-graphs-container', style={'display': 'none'})
    ])
])

@app.callback(
    [Output('tabs-content', 'children'),
     Output('day-filter-container', 'style'),
     Output('daytime-graphs-container', 'style')],
    [Input('tabs-navigation', 'value'),
     Input('store-id-dropdown', 'value'), # Now passing Store Name
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value')]
)
def render_tab_content(active_tab, selected_store_name, start_date, end_date, account_filter):
    # Default styles
    hide = {'display': 'none'}
    show_flex = {'display': 'flex', 'marginLeft': '40px'}
    show_block = {'display': 'block'}

    if active_tab == 'tab-store':
        return update_store_analysis(selected_store_name, start_date, end_date, account_filter), hide, hide
    elif active_tab == 'tab-customer':
        return update_customer_analysis(selected_store_name, account_filter, start_date, end_date), hide, hide
    else:
        # For Daytime tab, tabs-content is empty; we show the specific daytime containers
        return None, show_flex, show_block

@app.callback(
    Output('daytime-graphs-container', 'children'),
    [Input('store-id-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value'),
     Input('daytime-day-filter', 'value')]
)
def update_daytime_graphs(selected_store_name, start_date, end_date, account_filter, day_of_week):
    return render_daytime_analysis_charts(selected_store_name, start_date, end_date, account_filter, day_of_week)

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

    if not df_cat_trends.empty:
        fig_cat = px.line(
            df_cat_trends, x='month_year', y='order_count', color='customer_category',
            title='Order Volume Trends by Customer Category',
            labels={'month_year': 'Month', 'order_count': 'Orders', 'customer_category': 'Category'},
            category_orders={'customer_category': CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            markers=True,
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
        # Clip values at 150 to create a single overflow bin for all orders > $150
        df_hist_data = df_totals.copy()
        df_hist_data['Total'] = df_hist_data['Total'].clip(upper=150)

        fig_hist = px.histogram(
            df_hist_data, x='Total',
            color='customer_category',
            category_orders={'customer_category': CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            title='Distribution of Order Totals by Category',
            labels={'Total': 'Order Total ($)', 'customer_category': 'Category'},
            template='plotly_dark',
            nbins=30 # This creates consistent $5 bins for the 0-150 range
        )
        fig_hist.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            bargap=0.1,
            xaxis=dict(
                tickmode='array',
                tickvals=[0, 50, 100, 150],
                ticktext=['$0', '$50', '$100', '$150+']
            )
        )
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

def update_customer_analysis(selected_store, account_filter, start_date, end_date):
    df_cust = fetch_customer_stats(selected_store, account_filter)
    df_top = fetch_top_customers(selected_store, account_filter)
    df_overdue = fetch_overdue_customers(selected_store, account_filter)
    df_new = fetch_new_customers_trend(selected_store, account_filter, start_date, end_date)
    df_returning = fetch_last_order_trend(selected_store, account_filter, start_date, end_date)
    
    if df_cust.empty and df_top.empty and df_overdue.empty and df_new.empty and df_returning.empty:
        return html.Div("No customer data available.", style={'color': '#7FDBFF', 'textAlign': 'center'})

    fig_count = px.pie(
        df_cust, values='customer_count', names='customer_category',
        color='customer_category',
        title='Customer Distribution by Category',
        template='plotly_dark',
        hole=0.4,
        category_orders={'customer_category': CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS
    )
    
    fig_spend = px.pie(
        df_cust, values='total_spend', names='customer_category',
        color='customer_category',
        title='Total Spend by Category',
        template='plotly_dark',
        hole=0.4,
        category_orders={'customer_category': CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS
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

    # Overdue Customers Bar Chart
    overdue_hover_cols = ['median_spend', 'order_count', 'median_days_between_orders', 'recency', 'total_spend']
    fig_overdue = px.bar(
        df_overdue, 
        x='Name', 
        y='days_past_expected',
        color='customer_category',
        category_orders={'customer_category': CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
        title='Customers Past Expected Visit (Days)',
        labels={'days_past_expected': 'Days Overdue', 'Name': 'Customer', 'customer_category': 'Category'},
        custom_data=overdue_hover_cols,
        template='plotly_dark'
    )
    fig_overdue.update_traces(
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Days Overdue: %{y:.0f}<br>"
            "Total Lifetime Spend: $%{customdata[4]:,.2f}<br>"
            "Median Order Total: $%{customdata[0]:,.2f}<br>"
            "Order Count: %{customdata[1]}<br>"
            "Median Interval: %{customdata[2]:.1f} days<br>"
            "Last Order: %{customdata[3]:.0f} days ago"
            "<extra></extra>"
        )
    )
    fig_overdue.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

    # New Customer Acquisition Trend
    if not df_new.empty:
        fig_new = px.bar(
            df_new, x='month_year', y='new_customer_count', color='customer_category',
            title='New Customer Acquisition Trend',
            labels={'month_year': 'Month', 'new_customer_count': 'New Customers', 'customer_category': 'Category'},
            category_orders={'customer_category': CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template='plotly_dark'
        )
        fig_new.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig_new = px.scatter(title="No acquisition data available.", template='plotly_dark')
        fig_new.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

    # Last Order Activity Trend
    if not df_returning.empty:
        fig_returning = px.bar(
            df_returning, x='month_year', y='last_order_count', color='customer_category',
            title='Last Order Activity Trend',
            labels={'month_year': 'Month', 'last_order_count': 'Customers', 'customer_category': 'Category'},
            category_orders={'customer_category': CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template='plotly_dark'
        )
        fig_returning.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig_returning = px.scatter(title="No activity data available.", template='plotly_dark')
        fig_returning.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

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
        html.Div([dcc.Graph(id='top-customer-bar-line', figure=fig_top)], style={'width': '50%'}),
        html.Div([dcc.Graph(id='overdue-customer-bar', figure=fig_overdue)], style={'width': '50%'})
    ], style={'display': 'flex'}),
    html.Div([
        html.Div([dcc.Graph(id='new-customer-trend', figure=fig_new)], style={'width': '50%'}),
        html.Div([dcc.Graph(id='last-order-trend', figure=fig_returning)], style={'width': '50%'})
    ], style={'display': 'flex'}),)

def render_daytime_analysis_charts(selected_store_name, start_date, end_date, account_filter, day_of_week):
    """
    Generates the actual histograms for the DayTime Analysis tab.
    """
    # Default value for the pattern-matched input if it doesn't exist yet
    day_val = day_of_week if day_of_week is not None else 'All'

    df_placed = fetch_daytime_data(selected_store_name, start_date, end_date, account_filter, day_val)
    df_collected = fetch_collection_data(selected_store_name, start_date, end_date, account_filter, day_val)

    if df_placed.empty and df_collected.empty:
        return html.Div("No daytime or collection data available.", style={'color': '#7FDBFF', 'textAlign': 'center', 'marginTop': '40px'})

    # Order Placed Distribution
    fig_placed = px.histogram(
        df_placed, 
        x='placed_hour', 
        color='customer_category',
        category_orders={
            'customer_category': CATEGORY_ORDER,
            'placed_hour': [f"{i:02d}" for i in range(7, 19)]
        },
        color_discrete_map=CATEGORY_COLORS,
        title='Order Placed Distribution (7AM - 7PM)',
        labels={'placed_hour': 'Hour of Day (24h)', 'customer_category': 'Category'},
        template='plotly_dark'
    )
    
    # Order Collected Distribution
    fig_collected = px.histogram(
        df_collected, 
        x='collected_hour', 
        color='customer_category',
        category_orders={
            'customer_category': CATEGORY_ORDER,
            'collected_hour': [f"{i:02d}" for i in range(7, 19)]
        },
        color_discrete_map=CATEGORY_COLORS,
        title='Order Collected Distribution (7AM - 7PM)',
        labels={'collected_hour': 'Hour of Day (24h)', 'customer_category': 'Category'},
        template='plotly_dark'
    )
    
    for fig in [fig_placed, fig_collected]:
        fig.update_layout(
            plot_bgcolor='#111111',
            paper_bgcolor='#111111',
            font_color='#7FDBFF',
            bargap=0.1,
            xaxis=dict(type='category'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    
    return html.Div([
        html.Div([
            dcc.Graph(id='placed-daytime-histogram', figure=fig_placed)
        ], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([
            dcc.Graph(id='collected-daytime-histogram', figure=fig_collected)
        ], style={'width': '50%', 'display': 'inline-block'})
    ], style={'display': 'flex'})

if __name__ == '__main__':
    app.run(debug=True)