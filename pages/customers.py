import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Any
from database_utils import (
    fetch_customer_stats,
    fetch_top_customers,
    fetch_overdue_customers,
    fetch_customer_intervals,
    fetch_customer_ltv,
    fetch_customers_list,
    fetch_customer_monthly_sales,
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
def update_customers(
    selected_store: str,
    account_filter: str,
    start_date: str,
    end_date: str,
) -> Any:
    df_cust = fetch_customer_stats(selected_store, account_filter, start_date, end_date)
    df_top = fetch_top_customers(selected_store, account_filter)
    df_overdue = fetch_overdue_customers(
        selected_store, account_filter, start_date=start_date, end_date=end_date
    )
    df_intervals = fetch_customer_intervals(
        selected_store, account_filter, start_date, end_date
    )
    df_ltv = fetch_customer_ltv(selected_store, account_filter, start_date, end_date)

    if (
        df_cust.empty
        and df_top.empty
        and df_overdue.empty
        and df_intervals.empty
        and df_ltv.empty
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

    if not df_ltv.empty:
        df_ltv_hist = df_ltv.copy()
        median_ltv = df_ltv_hist["total_spend"].median()
        df_ltv_hist["total_spend"] = df_ltv_hist["total_spend"].clip(lower=0, upper=500)
        fig_ltv = px.histogram(
            df_ltv_hist,
            x="total_spend",
            color="customer_category",
            title="Customer Lifetime Value Distribution",
            labels={
                "total_spend": "Lifetime Value ($)",
                "customer_category": "Category",
            },
            category_orders={"customer_category": CATEGORY_ORDER},
            color_discrete_map=CATEGORY_COLORS,
            template="plotly_dark",
            nbins=40,
        )
        if not pd.isna(median_ltv):
            fig_ltv.add_vline(
                x=median_ltv,
                line_width=2,
                line_dash="dash",
                line_color="white",
                annotation_text=f"Median: ${median_ltv:.2f}",
                annotation_position="top right",
            )
        fig_ltv.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            bargap=0.1,
            xaxis=dict(
                tickmode="array",
                tickvals=[0, 250, 500, 750, 1000],
                ticktext=["$0", "$250", "$500", "$750", "$1,000+"],
            ),
        )
    else:
        fig_ltv = px.scatter(
            title="No lifetime value data available.", template="plotly_dark"
        )
        fig_ltv.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    for fig in [fig_count, fig_spend, fig_top]:
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    df_customers = fetch_customers_list(selected_store, account_filter)
    if not df_customers.empty:
        customer_options = [
            {"label": row["display_name"], "value": f"{row['Store ID']}_{row['Customer ID']}"}
            for _, row in df_customers.iterrows()
        ]
        default_customer_val = customer_options[0]["value"]
    else:
        customer_options = []
        default_customer_val = None

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
                        [dcc.Graph(id="cust-ltv-histogram", figure=fig_ltv)],
                        style={"width": "50%"},
                    ),
                ],
                style={"display": "flex"},
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="cust-interval-histogram", figure=fig_intervals)],
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
                        [
                            html.Label(
                                "Select Customer:",
                                style={
                                    "color": "#7FDBFF",
                                    "marginBottom": "10px",
                                    "display": "block",
                                    "fontWeight": "bold",
                                },
                            ),
                            dcc.Dropdown(
                                id="customer-sales-dropdown",
                                options=customer_options,
                                value=default_customer_val,
                                style={
                                    "width": "100%",
                                    "color": "#111111",
                                    "marginTop": "10px",
                                },
                            ),
                        ],
                        style={"width": "25%", "padding": "20px", "boxSizing": "border-box"},
                    ),
                    html.Div(
                        [dcc.Graph(id="customer-sales-graph")],
                        style={"width": "75%"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "marginTop": "20px"},
            ),
        ]
    )


@callback(
    Output("customer-sales-graph", "figure"),
    [
        Input("customer-sales-dropdown", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
    ],
)
def update_customer_sales_graph(
    selected_customer_val: Optional[str],
    start_date: str,
    end_date: str,
) -> Any:
    if not selected_customer_val:
        fig = px.scatter(title="No customer selected.", template="plotly_dark")
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
        return fig

    try:
        store_id_str, customer_id_str = selected_customer_val.split("_", 1)
        store_id = int(store_id_str)
        customer_id = int(customer_id_str)
    except ValueError:
        fig = px.scatter(title="Invalid customer selected.", template="plotly_dark")
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
        return fig

    df_sales = fetch_customer_monthly_sales(
        customer_id=customer_id,
        store_id=store_id,
        start_date=start_date,
        end_date=end_date,
    )

    if df_sales.empty:
        fig = px.scatter(
            title="No sales data found for the selected customer.",
            template="plotly_dark",
        )
        fig.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )
        return fig

    fig = px.bar(
        df_sales,
        x="month_year",
        y="total_sales",
        title="Monthly Sales Over Time",
        labels={"month_year": "Month-Year", "total_sales": "Total Sales ($)"},
        template="plotly_dark",
    )
    fig.update_layout(
        plot_bgcolor="#111111",
        paper_bgcolor="#111111",
        font_color="#7FDBFF",
    )
    fig.update_traces(
        marker_color="#00CC96",
        hovertemplate="Month: %{x}<br>Sales: $%{y:,.2f}<extra></extra>",
    )
    return fig
