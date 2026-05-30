import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from database_utils import (
    fetch_item_pieces_by_week,
    fetch_unique_items,
    fetch_top_items,
    fetch_top_item_pairs,
)

dash.register_page(__name__, path="/items", name="Items Analysis", order=5)

layout = html.Div(
    [
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
                html.Div(id="items-content", style={"width": "80%"}),
            ],
            style={"display": "flex", "marginTop": "20px"},
        )
    ]
)


@callback(
    Output("items-content", "children"),
    [
        Input("store-id-dropdown", "value"),
        Input("date-range-picker", "start_date"),
        Input("date-range-picker", "end_date"),
        Input("account-type-dropdown", "value"),
        Input("item-selection-dropdown", "value"),
    ],
)
def update_items(
    selected_store_name, start_date, end_date, account_filter, selected_items
):
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
        fig_top_items = px.bar(
            df_top_items,
            x="order_count",
            y="Item",
            orientation="h",
            title="Top 20 Items by Order Frequency",
            labels={"order_count": "Number of Orders", "Item": "Item"},
            template="plotly_dark",
        )
        fig_top_items.update_layout(
            yaxis={"categoryorder": "total ascending"},
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
        fig_top_pairs = px.bar(
            df_top_pairs,
            x="pair_count",
            y="item_pair",
            orientation="h",
            title="Top 20 Item Pairs by Order Frequency",
            labels={"pair_count": "Number of Orders", "item_pair": "Item Pair"},
            template="plotly_dark",
        )
        fig_top_pairs.update_layout(
            yaxis={"categoryorder": "total ascending"},
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
            dcc.Graph(id="items-pieces-line-chart", figure=fig_pieces),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="top-items-bar-chart", figure=fig_top_items)],
                        style={"width": "50%", "display": "inline-block"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(
                                id="top-item-pairs-bar-chart", figure=fig_top_pairs
                            )
                        ],
                        style={"width": "50%", "display": "inline-block"},
                    ),
                ],
                style={"display": "flex", "marginTop": "20px"},
            ),
        ]
    )
