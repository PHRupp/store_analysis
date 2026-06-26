import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
from typing import Any
from database_utils import fetch_monthly_sales

dash.register_page(__name__, path="/", name="Enterprise Analysis", order=1)

CATEGORY_ORDER = [
    "1 One Time",
    "2-3 Testing",
    "4-9 Comfortable",
    "10-19 Regular",
    "20-49 Super Regular",
    "50+ Big Dawgs",
]
CATEGORY_COLORS = {
    cat: px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
    for i, cat in enumerate(CATEGORY_ORDER)
}

layout = html.Div([html.Div(id="enterprise-content")])


@callback(
    Output("enterprise-content", "children"),
    [
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("account-type-dropdown", "value"),
    ],
)
def update_enterprise(start_date: str, end_date: str, account_filter: str) -> Any:
    # Enterprise overview enforces aggregation over all stores
    selected_store_name = "All"
    df_sales = fetch_monthly_sales(
        selected_store_name, start_date, end_date, account_filter
    )

    title = "Monthly Sales Overview - Enterprise"

    if not df_sales.empty:
        df_line = df_sales.groupby("month_year")["total_pieces"].sum().reset_index()

        fig = px.bar(
            df_sales,
            x="month_year",
            y="total_sales",
            color="account_type",
            title=title,
            labels={
                "month_year": "Month (YYYY-MM)",
                "total_sales": "Total Sales ($)",
                "account_type": "Account Type",
            },
            template="plotly_dark",
        )
        fig.add_trace(
            go.Scatter(
                x=df_line["month_year"],
                y=df_line["total_pieces"],
                name="Total Pieces",
                mode="lines+markers",
                line=dict(color="#FFD700", width=3),
                yaxis="y2",
            )
        )
        fig.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            yaxis2=dict(
                title="Total Pieces",
                overlaying="y",
                side="right",
                showgrid=False,
                color="#FFD700",
                rangemode="tozero",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig = px.scatter(
            title="No data available for the selected criteria.", template="plotly_dark"
        )
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    return html.Div([dcc.Graph(id="enterprise-sales-bar-chart", figure=fig)])
