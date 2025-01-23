from dash import dcc, Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from Project.Simulator import Simulator

app = Dash()
agent = -1
simulator = Simulator(120, 120, 12, 200)


def set_layout(plt):
    app.layout = [html.Div(
        dbc.Row(
            [
                dbc.Col(html.Div(dcc.Graph(figure=plt, id="graph")), style={'width': 'auto'}),
                dbc.Col(html.Div([
                    html.Div(html.Label("text", id="log"),
                             style={'width': 200, 'height': 500, 'margin-top': 150, 'overflow': 'auto'}),
                    html.Div(dcc.Dropdown(id='agent_choice', options=[
                        {'label': 'All', 'value': -1},
                        {'label': 'A', 'value': 1},
                        {'label': 'B', 'value': 2}
                    ], value=-1, style={'textAlign': 'center', 'margin-right': 15, 'width': 150})),
                    dbc.Input(id='count', value=1, type='number', style={'margin-right': 15}),
                    html.Button('Next', id='submit-next', n_clicks=0,
                                style={'margin-right': 15, 'width': 150, 'margin-top': 15})
                ], style={'display': 'inline-block'}), style={'width': 'auto'})
            ], justify="evenly", style={'display': 'inline-flex', 'width': 'auto'}
        ), style={'display': 'inline-flex', 'width': 'auto'}
    )]


@callback(
    Output('graph', 'figure'),
    Input('submit-next', 'n_clicks'),
    State('count', 'value'),
    prevent_initial_call=True
)
def update_graph(n_clicks, value):
    print("Update!", n_clicks, value)
    for _ in range(value):
        plt = simulator.simulate_next_step(agent)
    return plt


@callback(
    Input('agent_choice', 'value'),
    prevent_initial_call=True
)
def choice_agent(value):
    print("Agent:", value)
    agent = value


# TODO: Textfeld als secondary output mit Events
set_layout(simulator.print_map())
app.run(debug=True)
