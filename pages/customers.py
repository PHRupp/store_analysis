import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database_utils import (
    fetch_customer_stats,
    fetch_top_customers,
    fetch_overdue_customers,
    fetch_new_customers_trend,
    fetch_last_order_trend,
    fetch_customer_intervals,
)

dash.register_page(__name__, path="/customers", name="Customer Analysis", order=3)

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

layout = html.Div([html.Div(id="customers-content")])


@callback(
    Output("customers-content", "children"),
    [
        Input("store-id-dropdown", "value"),
        Input("account-type-dropdown", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
    ],
)
def update_customers(selected_store, account_filter, start_date, end_date):
    df_cust = fetch_customer_stats(selected_store, account_filter, start_date, end_date)
    df_top = fetch_top_customers(selected_store, account_filter)
    df_overdue = fetch_overdue_customers(
        selected_store, account_filter, start_date=start_date, end_date=end_date
    )
    df_new = fetch_new_customers_trend(
        selected_store, account_filter, start_date, end_date
    )
    df_returning = fetch_last_order_trend(
        selected_store, account_filter, start_date, end_date
    )
    df_intervals = fetch_customer_intervals(
        selected_store, account_filter, start_date, end_date
    )

    if (
        df_cust.empty
        and df_top.empty
        and df_overdue.empty
        and df_new.empty
        and df_returning.empty
        and df_intervals.empty
    ):
        return html.Div(
            "No customer data available.",
            style={"color": "#7FDBFF", "textAlign": "center"},
        )

    fig_count = px.pie(
        df_cust,
        values="customer_count",
        names="customer_category",
        color="customer_category",
        title="Customer Distribution by Category",
        template="plotly_dark",
        hole=0.4,
        category_orders={"customer_category": CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
    )

    fig_spend = px.pie(
        df_cust,
        values="total_spend",
        names="customer_category",
        color="customer_category",
        title="Total Spend by Category",
        template="plotly_dark",
        hole=0.4,
        category_orders={"customer_category": CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
    )

    custom_hover_cols = [
        "customer_category",
        "order_count",
        "discount",
        "recency",
        "median_days_between_orders",
    ]
    common_hover = "Category: %{customdata[0]}<br>Order Count: %{customdata[1]}<br>Discount: %{customdata[2]}%<br>Last Order: %{customdata[3]:.0f} days ago<br>Median Interval: %{customdata[4]:.1f} days<extra></extra>"

    fig_top = px.bar(
        df_top,
        x="Name",
        y="total_spend",
        title="Top Customers: Lifetime Value vs Median Order Amount",
        labels={"total_spend": "Total Spending"},
        custom_data=custom_hover_cols,
        template="plotly_dark",
    )
    fig_top.update_traces(
        marker_color="#00CC96",
        hovertemplate="Total Spend: $%{y:,.2f}<br>" + common_hover,
        selector=dict(type="bar"),
    )
    fig_top.add_trace(
        go.Scatter(
            x=df_top["Name"],
            y=df_top["median_spend"],
            name="Median Spend",
            line=dict(color="#7FDBFF", width=3),
            mode="lines+markers",
            customdata=df_top[custom_hover_cols],
            hovertemplate="Median Spend: $%{y:,.2f}<br>" + common_hover,
            yaxis="y2",
        )
    )
    fig_top.update_layout(
        hovermode="x unified",
        yaxis=dict(title="Total Spending ($)"),
        yaxis2=dict(
            title="Median Spend ($)",
            overlaying="y",
            side="right",
            showgrid=False,
            color="#7FDBFF",
        ),
    )

    overdue_hover_cols = [
        "median_spend",
        "order_count",
        "median_days_between_orders",
        "recency",
        "total_spend",
    ]
    fig_overdue = px.bar(
        df_overdue,
        x="Name",
        y="days_past_expected",
        color="customer_category",
        category_orders={"customer_category": CATEGORY_ORDER},
        color_discrete_map=CATEGORY_COLORS,
        title="Customers Past Expected Visit (Days)",
        labels={
            "days_past_expected": "Days Overdue",
            "Name": "Customer",
            "customer_category": "Category",
        },
        custom_data=overdue_hover_cols,
        template="plotly_dark",
    )
    fig_overdue.update_traces(
        hovertemplate="<b>%{x}</b><br>Days Overdue: %{y:.0f}<br>Total Lifetime Spend: $%{customdata[4]:,.2f}<br>Median Order Total: $%{customdata[0]:,.2f}<br>Order Count: %{customdata[1]}<br>Median Interval: %{customdata[2]:.1f} days<br>Last Order: %{customdata[3]:.0f} days ago<extra></extra>"
    )
    fig_overdue.update_layout(
        plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
    )

    if not df_new.empty:
        fig_new = px.bar(
            df_new,
            x="month_year",
            y="new_customer_count",
            color="customer_category",
            title="New Customer Acquisition Trend",
            labels={
                "month_year": "Month",
                "new_customer_count": "New Customers",
                "customer_category": "Category",
            },
            category_orders={"customer_category": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template="plotly_dark",
        )
        fig_new.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
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

    if not df_returning.empty:
        avg_returning = (
            df_returning.groupby("month_year")["last_order_count"].sum().mean()
        )
        fig_returning = px.bar(
            df_returning,
            x="month_year",
            y="last_order_count",
            color="customer_category",
            title="Last Order Activity Trend",
            labels={
                "month_year": "Month",
                "last_order_count": "Customers",
                "customer_category": "Category",
            },
            category_orders={"customer_category": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template="plotly_dark",
        )
        if not pd.isna(avg_returning):
            fig_returning.add_hline(
                y=avg_returning,
                line_width=2,
                line_dash="dash",
                line_color="white",
                annotation_text=f"Avg: {avg_returning:.1f}",
                annotation_position="top right",
            )
        fig_returning.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig_returning = px.scatter(
            title="No activity data available.", template="plotly_dark"
        )
        fig_returning.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    if not df_intervals.empty:
        df_hist_data = df_intervals.copy()
        df_hist_data["median_days_between_orders"] = df_hist_data[
            "median_days_between_orders"
        ].clip(upper=180)
        df_avg_calc = df_intervals[df_intervals["order_count"] >= 10]
        avg_interval = df_avg_calc["median_days_between_orders"].median()
        fig_intervals = px.histogram(
            df_hist_data,
            x="median_days_between_orders",
            color="customer_category",
            title="Customer Distribution of Days Between Orders",
            labels={
                "median_days_between_orders": "Median Days Between Orders",
                "customer_category": "Category",
            },
            category_orders={"customer_category": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template="plotly_dark",
            nbins=36,
        )
        if not pd.isna(avg_interval):
            fig_intervals.add_vline(
                x=avg_interval,
                line_width=2,
                line_dash="dash",
                line_color="white",
                annotation_text=f"Avg (10+ Orders): {avg_interval:.1f} days",
                annotation_position="top right",
            )
        fig_intervals.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            bargap=0.1,
            xaxis=dict(
                tickmode="array",
                tickvals=[0, 30, 60, 90, 120, 150, 180],
                ticktext=["0", "30", "60", "90", "120", "150", "180+"],
            ),
        )
    else:
        fig_intervals = px.scatter(
            title="No interval data available.", template="plotly_dark"
        )
        fig_intervals.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    for fig in [fig_count, fig_spend, fig_top]:
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="cust-count-pie", figure=fig_count)],
                        style={"width": "50%", "display": "inline-block"},
                    ),
                    html.Div(
                        [dcc.Graph(id="cust-spend-pie", figure=fig_spend)],
                        style={"width": "50%", "display": "inline-block"},
                    ),
                ],
                style={"display": "flex"},
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="cust-top-bar-line", figure=fig_top)],
                        style={"width": "50%"},
                    ),
                    html.Div(
                        [dcc.Graph(id="cust-overdue-bar", figure=fig_overdue)],
                        style={"width": "50%"},
                    ),
                ],
                style={"display": "flex"},
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="cust-new-trend", figure=fig_new)],
                        style={"width": "50%"},
                    ),
                    html.Div(
                        [dcc.Graph(id="cust-last-order-trend", figure=fig_returning)],
                        style={"width": "50%"},
                    ),
                ],
                style={"display": "flex"},
            ),
            html.Div([dcc.Graph(id="cust-interval-histogram", figure=fig_intervals)]),
        ]
    )
