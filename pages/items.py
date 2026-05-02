import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from database_utils import fetch_daytime_data, fetch_collection_data, fetch_order_totals

dash.register_page(__name__, path='/orders', name='Orders Analysis', order=4)

CATEGORY_ORDER = [
    '1 One Time', '2-3 Testing', '4-9 Comfortable', '10-19 Regular', '20-49 Super Regular', '50+ Big Dawgs'
]
CATEGORY_COLORS = {
    cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
    for i, cat in enumerate(CATEGORY_ORDER)
}

layout = html.Div([
    html.Div(id='orders-content')
])

@callback(
    Output('orders-content', 'children'),
    [Input('store-id-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value')]
)
def update_orders(selected_store_name, start_date, end_date, account_filter):
    day_val = 'All'

    df_placed = fetch_daytime_data(selected_store_name, start_date, end_date, account_filter, day_val)
    df_collected = fetch_collection_data(selected_store_name, start_date, end_date, account_filter, day_val)
    df_totals = fetch_order_totals(selected_store_name, start_date, end_date, account_filter)

    if df_placed.empty and df_collected.empty:
        return html.Div("No daytime or collection data available.", style={'color': '#7FDBFF', 'textAlign': 'center', 'marginTop': '40px'})

    fig_placed = px.bar(
        df_placed, x='placed_hour', y='order_count', color='customer_category',
        category_orders={'customer_category': CATEGORY_ORDER, 'placed_hour': [f"{i:02d}" for i in range(7, 19)]},
        color_discrete_map=CATEGORY_COLORS, title='Order Placed Distribution (7AM - 7PM)',
        labels={'placed_hour': 'Hour of Day (24h)', 'customer_category': 'Category', 'order_count': 'Orders'},
        template='plotly_dark'
    )
    
    fig_collected = px.bar(
        df_collected, x='collected_hour', y='order_count', color='customer_category',
        category_orders={'customer_category': CATEGORY_ORDER, 'collected_hour': [f"{i:02d}" for i in range(7, 19)]},
        color_discrete_map=CATEGORY_COLORS, title='Order Collected Distribution (7AM - 7PM)',
        labels={'collected_hour': 'Hour of Day (24h)', 'customer_category': 'Category', 'order_count': 'Orders'},
        template='plotly_dark'
    )
    
    for fig in [fig_placed, fig_collected]:
        fig.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            bargap=0.1, xaxis=dict(type='category'), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    
    if not df_totals.empty:
        df_hist_data = df_totals.copy()
        df_hist_data['Total'] = df_hist_data['Total'].clip(lower=-5, upper=150)
        fig_hist = px.histogram(
            df_hist_data, x='Total', color='customer_category',
            category_orders={'customer_category': CATEGORY_ORDER}, color_discrete_map=CATEGORY_COLORS,
            title='Distribution of Order Totals by Category', labels={'Total': 'Order Total ($)', 'customer_category': 'Category'},
            template='plotly_dark', nbins=31
        )
        fig_hist.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF', bargap=0.1,
            xaxis=dict(tickmode='array', tickvals=[-5, 0, 25, 50, 75, 100, 125, 150], ticktext=['< $0', '$0', '$25', '$50', '$75', '$100', '$125', '$150+'])
        )
    else:
        fig_hist = px.scatter(title="No order total data available.", template='plotly_dark')
        fig_hist.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

    return html.Div([
        html.Div([
            html.Div([dcc.Graph(id='orders-placed-histogram', figure=fig_placed)], style={'width': '50%', 'display': 'inline-block'}),
            html.Div([dcc.Graph(id='orders-collected-histogram', figure=fig_collected)], style={'width': '50%', 'display': 'inline-block'})
        ], style={'display': 'flex'}),
        html.Div([dcc.Graph(id='orders-order-totals-histogram', figure=fig_hist)])
    ])