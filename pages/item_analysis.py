import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from typing import Any, List, Optional
from database_utils import (
    fetch_item_pieces_by_week,
    fetch_unique_items,
    fetch_top_items,
    fetch_top_item_pairs,
    fetch_total_order_count,
)

dash.register_page(__name__, path="/items", name="Items Analysis", order=5)

layout = html.Div(
    [
        html.Div(id="items-top-content", style={"marginTop": "20px"}),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Select Items:", style={"color": "#7FDBFF"}),
                        dcc.Dropdown(
                            id="item-selection-dropdown",
                            options=[
                                {"label": item, "value": item}
                                for item in fetch_unique_items()
                            ],
                            multi=True,
                            placeholder="All Items (Select to filter)",
                            style={"color": "#111111", "marginTop": "10px"},
                        ),
                    ],
                    style={"width": "20%", "paddingRight": "20px"},
                ),
                html.Div(id="items-bottom-content", style={"width": "80%"}),
            ],
            style={"display": "flex", "marginTop": "20px"},
        ),
    ]
)


@callback(
    [
        Output("items-top-content", "children"),
        Output("items-bottom-content", "children"),
    ],
    [
        Input("store-id-dropdown", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("account-type-dropdown", "value"),
        Input("item-selection-dropdown", "value"),
    ],
)
def update_items(
    selected_store_name: str,
    start_date: str,
    end_date: str,
    account_filter: str,
    selected_items: Optional[List[str]],
) -> Any:
    df_pieces = fetch_item_pieces_by_week(
        selected_store_name, start_date, end_date, account_filter, selected_items
    )

    # Market basket analysis plots (unaffected by selected_items)
    df_top_items = fetch_top_items(
        selected_store_name, start_date, end_date, account_filter
    )
    df_top_pairs = fetch_top_item_pairs(
        selected_store_name, start_date, end_date, account_filter
    )
    total_orders = fetch_total_order_count(
        selected_store_name, start_date, end_date, account_filter
    )

    if not df_top_items.empty and total_orders > 0:
        df_top_items["percent_orders"] = (
            df_top_items["order_count"] / total_orders
        ) * 100

    if not df_top_pairs.empty and total_orders > 0:
        df_top_pairs["percent_orders"] = (
            df_top_pairs["pair_count"] / total_orders
        ) * 100

    if not df_pieces.empty:
        fig_pieces = px.line(
            df_pieces,
            x="week",
            y="total_pieces",
            color="account_type",
            title="Total Pieces Over Time by Week",
            labels={
                "week": "Week",
                "total_pieces": "Total Pieces",
                "account_type": "Account Type",
            },
            template="plotly_dark",
            markers=True,
        )
        fig_pieces.update_layout(
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
    else:
        fig_pieces = px.scatter(
            title="No data available for pieces over time.", template="plotly_dark"
        )
        fig_pieces.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    # Top Items Bar Chart
    if not df_top_items.empty:
        x_col = "percent_orders" if total_orders > 0 else "order_count"
        x_label = "% of Orders" if total_orders > 0 else "Number of Orders"
        fig_top_items = px.bar(
            df_top_items,
            x=x_col,
            y="Item",
            orientation="h",
            title="Top 20 Items by Order Frequency",
            labels={x_col: x_label, "Item": "Item"},
            template="plotly_dark",
        )
        if total_orders > 0:
            fig_top_items.update_traces(hovertemplate="%{y}: %{x:.2f}%<extra></extra>")

        fig_top_items.update_layout(
            yaxis={"categoryorder": "total ascending", "dtick": 1},
            xaxis={"ticksuffix": "%"} if total_orders > 0 else {},
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
        )
    else:
        fig_top_items = px.scatter(
            title="No top items data available.", template="plotly_dark"
        )
        fig_top_items.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    # Top Pairs Bar Chart
    if not df_top_pairs.empty:
        x_col_pairs = "percent_orders" if total_orders > 0 else "pair_count"
        x_label_pairs = "% of Orders" if total_orders > 0 else "Number of Orders"
        fig_top_pairs = px.bar(
            df_top_pairs,
            x=x_col_pairs,
            y="item_pair",
            orientation="h",
            title="Top 20 Item Pairs by Order Frequency",
            labels={x_col_pairs: x_label_pairs, "item_pair": "Item Pair"},
            template="plotly_dark",
        )
        if total_orders > 0:
            fig_top_pairs.update_traces(hovertemplate="%{y}: %{x:.2f}%<extra></extra>")

        fig_top_pairs.update_layout(
            yaxis={"categoryorder": "total ascending", "dtick": 1},
            xaxis={"ticksuffix": "%"} if total_orders > 0 else {},
            plot_bgcolor="#111111",
            paper_bgcolor="#111111",
            font_color="#7FDBFF",
        )
    else:
        fig_top_pairs = px.scatter(
            title="No top item pairs data available.", template="plotly_dark"
        )
        fig_top_pairs.update_layout(
            plot_bgcolor="#111111", paper_bgcolor="#111111", font_color="#7FDBFF"
        )

    return html.Div(
        [
            html.Div(
                [dcc.Graph(id="top-items-bar-chart", figure=fig_top_items)],
                style={"width": "50%", "display": "inline-block"},
            ),
            html.Div(
                [dcc.Graph(id="top-item-pairs-bar-chart", figure=fig_top_pairs)],
                style={"width": "50%", "display": "inline-block"},
            ),
        ],
        style={"display": "flex"},
    ), dcc.Graph(id="items-pieces-line-chart", figure=fig_pieces)
