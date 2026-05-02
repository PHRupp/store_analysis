import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from database_utils import fetch_monthly_revenue, fetch_order_trends, fetch_category_order_trends, fetch_order_totals

dash.register_page(__name__, path='/store', name='Store Analysis', order=2)

CATEGORY_ORDER = [
    '1 One Time', '2-3 Testing', '4-9 Comfortable', '10-19 Regular', '20-49 Super Regular', '50+ Big Dawgs'
]
CATEGORY_COLORS = {
    cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)] 
    for i, cat in enumerate(CATEGORY_ORDER)
}

layout = html.Div([
    html.Div(id='store-content')
])

@callback(
    Output('store-content', 'children'),
    [Input('store-id-dropdown', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('account-type-dropdown', 'value')]
)
def update_store(selected_store_name, start_date, end_date, account_filter):
    df_revenue = fetch_monthly_revenue(selected_store_name, start_date, end_date, account_filter)
    df_trends = fetch_order_trends(selected_store_name, start_date, end_date, account_filter)
    df_cat_trends = fetch_category_order_trends(selected_store_name, start_date, end_date, account_filter)
    df_totals = fetch_order_totals(selected_store_name, start_date, end_date, account_filter)
    
    title = f'Monthly Revenue Overview - Store: {selected_store_name}'
    
    if not df_revenue.empty:
        df_line = df_revenue.groupby('month_year')['total_pieces'].sum().reset_index()

        fig = px.bar(
            df_revenue, x='month_year', y='total_revenue', color='account_type',
            title=title, labels={'month_year': 'Month (YYYY-MM)', 'total_revenue': 'Total Revenue ($)', 'account_type': 'Account Type'},
            template='plotly_dark'
        )
        fig.add_trace(go.Scatter(
            x=df_line['month_year'], y=df_line['total_pieces'], name='Total Pieces', mode='lines+markers',
            line=dict(color='#FFD700', width=3), yaxis='y2'
        ))
        fig.update_layout(
            plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF',
            yaxis2=dict(title='Total Pieces', overlaying='y', side='right', showgrid=False, color='#FFD700'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
    else:
        fig = px.scatter(title="No data available for the selected criteria.", template='plotly_dark')
        fig.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')
    
    if not df_trends.empty:
        fig_trends = go.Figure()
        fig_trends.add_trace(go.Scatter(
            x=df_trends['month_year'], y=df_trends['median_invoice'], name='Median Invoice',
            mode='lines+markers', line=dict(color='#00CC96', width=3)
        ))
        fig_trends.add_trace(go.Scatter(
            x=df_trends['month_year'], y=df_trends['order_count'], name='Order Count',
            mode='lines+markers', line=dict(color='#7FDBFF', width=3), yaxis='y2'
        ))
        fig_trends.update_layout(
            title='Monthly Order Trends: Median Value vs Volume', template='plotly_dark',
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
            category_orders={'customer_category': CATEGORY_ORDER}, color_discrete_map=CATEGORY_COLORS,
            markers=True, template='plotly_dark'
        )
        fig_cat.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    else:
        fig_cat = px.scatter(title="No category trend data available.", template='plotly_dark')
        fig_cat.update_layout(plot_bgcolor='#111111', paper_bgcolor='#111111', font_color='#7FDBFF')

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
        dcc.Graph(id='store-revenue-bar-chart', figure=fig),
        html.Div([
            html.Div(dcc.Graph(id='store-order-trends-chart', figure=fig_trends), style={'width': '50%'}),
            html.Div(dcc.Graph(id='store-category-trends-chart', figure=fig_cat), style={'width': '50%'})
        ], style={'display': 'flex'}),
        html.Div([dcc.Graph(id='store-order-totals-histogram', figure=fig_hist)])
    ])