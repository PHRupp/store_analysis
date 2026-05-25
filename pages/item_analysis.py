import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
from database_utils import fetch_item_pieces_by_week, fetch_unique_items

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

    return html.Div([dcc.Graph(id="items-pieces-line-chart", figure=fig_pieces)])
