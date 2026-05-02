import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from database_utils import fetch_daytime_data, fetch_collection_data

dash.register_page(__name__, path='/items', name='Items Analysis', order=4)

CATEGORY_ORDER = [
    '1 One Time', '2-3 Testing', '4-9 Comfortable', '10-19 Regular', '20-49 Super Regular', '50+ Big Dawgs'
]
CATEGORY_COLORS = {
    cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
    for i, cat in enumerate(CATEGORY_ORDER)
}

layout = html.Div([
    html.Div([
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
    ], style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '20px'}),
    html.Div(id='items-content')
])

@callback(
    Output('items-content', 'children'),
    [Input('store-id-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value'),
     Input('daytime-day-filter', 'value')]
)
def update_items(selected_store_name, start_date, end_date, account_filter, day_of_week):
    day_val = day_of_week if day_of_week is not None else 'All'

    df_placed = fetch_daytime_data(selected_store_name, start_date, end_date, account_filter, day_val)
    df_collected = fetch_collection_data(selected_store_name, start_date, end_date, account_filter, day_val)

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
    
    return html.Div([
        html.Div([dcc.Graph(id='items-placed-histogram', figure=fig_placed)], style={'width': '50%', 'display': 'inline-block'}),
        html.Div([dcc.Graph(id='items-collected-histogram', figure=fig_collected)], style={'width': '50%', 'display': 'inline-block'})
    ], style={'display': 'flex'})