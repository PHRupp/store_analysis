import dash
from dash import dcc, html, Input, Output, callback
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_utils import (
    fetch_monthly_revenue,
    fetch_order_trends,
    fetch_category_order_trends,
    fetch_new_customers_trend,
    fetch_last_order_trend,
)

dash.register_page(__name__, path="/store", name="Store Analysis", order=2)

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

layout = html.Div(
    [
        dcc.Graph(id="store-revenue-bar-chart"),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="store-revenue-per-piece-chart"),
                    style={"width": "50%"},
                ),
                html.Div(
                    dcc.Graph(id="store-pieces-per-order-chart"),
                    style={"width": "50%"},
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="store-order-trends-chart"),
                    style={"width": "50%"},
                ),
                html.Div(
                    dcc.Graph(id="store-category-trends-chart"),
                    style={"width": "50%"},
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="store-new-customer-trend"),
                    style={"width": "50%"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label(
                                    "Minimum Lapsed Days:",
                                    style={"color": "#7FDBFF", "marginRight": "15px"},
                                ),
                                dcc.Input(
                                    id="lapsed-days-input",
                                    type="number",
                                    value=90,
                                    min=0,
                                    style={
                                        "backgroundColor": "#222222",
                                        "color": "#7FDBFF",
                                        "border": "1px solid #333333",
                                        "borderRadius": "5px",
                                        "padding": "5px",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "justifyContent": "center",
                                "alignItems": "center",
                                "marginBottom": "10px",
                            },
                        ),
                        dcc.Graph(id="store-lapsed-customer-trend"),
                    ],
                    style={"width": "50%"},
                ),
            ],
            style={"display": "flex"},
        ),
    ]
)


@callback(
    [
        Output("store-revenue-bar-chart", "figure"),
        Output("store-revenue-per-piece-chart", "figure"),
        Output("store-pieces-per-order-chart", "figure"),
        Output("store-order-trends-chart", "figure"),
        Output("store-category-trends-chart", "figure"),
        Output("store-new-customer-trend", "figure"),
        Output("store-lapsed-customer-trend", "figure"),
    ],
    [
        Input("store-id-dropdown", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("account-type-dropdown", "value"),
        Input("lapsed-days-input", "value"),
    ],
)
def update_store(
    selected_store_name, start_date, end_date, account_filter, min_lapsed_days
):
    df_revenue = fetch_monthly_revenue(
        selected_store_name, start_date, end_date, account_filter
    )
    df_trends = fetch_order_trends(
        selected_store_name, start_date, end_date, account_filter
    )
    df_cat_trends = fetch_category_order_trends(
        selected_store_name, start_date, end_date, account_filter
    )
    df_new = fetch_new_customers_trend(
        selected_store_name, account_filter, start_date, end_date
    )
    df_lapsed = fetch_last_order_trend(
        selected_store_name, account_filter, start_date, end_date, min_lapsed_days
    )

    title = f"Monthly Revenue Overview - Store: {selected_store_name}"

    if not df_revenue.empty:
        df_line = df_revenue.groupby("month_year")["total_pieces"].sum().reset_index()

        fig = px.bar(
            df_revenue,
            x="month_year",
            y="total_revenue",
            color="account_type",
            title=title,
            labels={
                "month_year": "Month (YYYY-MM)",
                "total_revenue": "Total Revenue ($)",
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
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        df_ratio = (
            df_revenue.groupby("month_year")[["total_revenue", "total_pieces"]]
            .sum()
            .reset_index()
        )
        df_ratio["revenue_per_piece"] = (
            df_ratio["total_revenue"] / df_ratio["total_pieces"]
        )

        fig_ratio = px.line(
            df_ratio,
            x="month_year",
            y="revenue_per_piece",
            title="Revenue per Piece Over Time",
            labels={
                "month_year": "Month (YYYY-MM)",
                "revenue_per_piece": "Revenue per Piece ($)",
            },
            template="plotly_dark",
            markers=True,
        )
        fig_ratio.update_traces(line=dict(color="#00CC96", width=3))
        fig_ratio.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

        if not df_trends.empty:
            df_pieces_ratio = pd.merge(
                df_ratio, df_trends, on="month_year", how="inner"
            )
            df_pieces_ratio["pieces_per_order"] = (
                df_pieces_ratio["total_pieces"] / df_pieces_ratio["order_count"]
            )

            fig_pieces = go.Figure()
            fig_pieces.add_trace(
                go.Bar(
                    x=df_pieces_ratio["month_year"],
                    y=df_pieces_ratio["order_count"],
                    name="Order Count",
                    marker_color="purple",
                )
            )
            fig_pieces.add_trace(
                go.Scatter(
                    x=df_pieces_ratio["month_year"],
                    y=df_pieces_ratio["pieces_per_order"],
                    name="Pieces per Order",
                    mode="lines+markers",
                    line=dict(color="#FF851B", width=3),
                    yaxis="y2",
                )
            )
            fig_pieces.update_layout(
                title="Pieces per Order Over Time",
                template="plotly_dark",
                plot_bgcolor="#111111",
                paper_bgcolor="#111111",
                font_color="#7FDBFF",
                yaxis=dict(title="Order Count"),
                yaxis2=dict(
                    title="Pieces per Order",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    color="#FF851B",
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
        else:
            fig_pieces = px.scatter(
                title="No order data available for pieces per order.",
                template="plotly_dark",
            )
            fig_pieces.update_layout(
                plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
            )
    else:
        fig = px.scatter(
            title="No data available for the selected criteria.", template="plotly_dark"
        )
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
        fig_ratio = px.scatter(
            title="No data available for the selected criteria.", template="plotly_dark"
        )
        fig_ratio.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
        fig_pieces = px.scatter(
            title="No data available for the selected criteria.", template="plotly_dark"
        )
        fig_pieces.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    if not df_trends.empty:
        fig_trends = go.Figure()
        fig_trends.add_trace(
            go.Bar(
                x=df_trends["month_year"],
                y=df_trends["order_count"],
                name="Order Count",
                marker_color="purple",
            )
        )
        fig_trends.add_trace(
            go.Scatter(
                x=df_trends["month_year"],
                y=df_trends["median_invoice"],
                name="Median Invoice",
                mode="lines+markers",
                line=dict(color="#00CC96", width=3),
                yaxis="y2",
            )
        )
        fig_trends.update_layout(
            title="Monthly Order Trends: Median Value vs Volume",
            template="plotly_dark",
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            yaxis=dict(title="Order Count"),
            yaxis2=dict(
                title="Median Invoice ($)",
                overlaying="y",
                side="right",
                showgrid=False,
                color="#00CC96",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig_trends = px.scatter(
            title="No trend data available for the selected criteria.",
            template="plotly_dark",
        )
        fig_trends.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    if not df_cat_trends.empty:
        fig_cat = px.line(
            df_cat_trends,
            x="month_year",
            y="order_count",
            color="customer_category",
            title="Order Volume Trends by Customer Category",
            labels={
                "month_year": "Month",
                "order_count": "Orders",
                "customer_category": "Category",
            },
            category_orders={"customer_category": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            markers=True,
            template="plotly_dark",
        )
        fig_cat.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig_cat = px.scatter(
            title="No category trend data available.", template="plotly_dark"
        )
        fig_cat.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    if not df_new.empty:
        df_new_agg = (
            df_new.groupby("month_year")[
                ["new_customer_count", "returning_customer_count"]
            ]
            .sum()
            .reset_index()
        )
        df_new_agg["returning_percentage"] = (
            df_new_agg["returning_customer_count"] / df_new_agg["new_customer_count"]
        ) * 100
        df_new_agg["returning_percentage"] = df_new_agg["returning_percentage"].fillna(
            0
        )
        avg_new = df_new_agg["new_customer_count"].mean()

        fig_new = px.bar(
            df_new_agg,
            x="month_year",
            y="new_customer_count",
            title="New Customer Acquisition Trend",
            labels={"month_year": "Month", "new_customer_count": "New Customers"},
            template="plotly_dark",
        )
        if not pd.isna(avg_new):
            fig_new.add_hline(
                y=avg_new,
                line_width=2,
                line_dash="dash",
                line_color="white",
                annotation_text=f"Avg: {avg_new:.1f}",
                annotation_position="top left",
            )
        fig_new.add_trace(
            go.Scatter(
                x=df_new_agg["month_year"],
                y=df_new_agg["returning_percentage"],
                name="Returning %",
                mode="lines+markers",
                line=dict(color="#FFD700", width=3),
                yaxis="y2",
            )
        )
        fig_new.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            yaxis2=dict(
                title="Returning Customers (%)",
                overlaying="y",
                side="right",
                showgrid=False,
                color="#FFD700",
                range=[0, 100],
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig_new = px.scatter(
            title="No acquisition data available.", template="plotly_dark"
        )
        fig_new.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    if not df_lapsed.empty:
        df_lapsed_agg = (
            df_lapsed.groupby("month_year")["last_order_count"].sum().reset_index()
        )
        avg_lapsed = df_lapsed_agg["last_order_count"].mean()
        fig_lapsed = px.bar(
            df_lapsed_agg,
            x="month_year",
            y="last_order_count",
            title="Lapsed Customers by Last Order Month",
            labels={"month_year": "Month", "last_order_count": "Lapsed Customers"},
            template="plotly_dark",
        )
        if not pd.isna(avg_lapsed):
            fig_lapsed.add_hline(
                y=avg_lapsed,
                line_width=2,
                line_dash="dash",
                line_color="white",
                annotation_text=f"Avg: {avg_lapsed:.1f}",
                annotation_position="top right",
            )
        fig_lapsed.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
    else:
        fig_lapsed = px.scatter(
            title="No lapsed customer data available.", template="plotly_dark"
        )
        fig_lapsed.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    return fig, fig_ratio, fig_pieces, fig_trends, fig_cat, fig_new, fig_lapsed
