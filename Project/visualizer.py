from dash import dcc, Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from Project.Simulator import Simulator
from Project.SimulatedAgent import SimulatedAgent

app = Dash()
agent = -1
simulator = Simulator(120, 120, 12, 2000)
agents = simulator.get_agents()

@callback(
    Output('graph', 'figure'),
    Input('submit-next', 'n_clicks'),
    State('agent_choice', 'value'),
    State('count', 'value'),
    prevent_initial_call=True
)
def update_graph(n_clicks, agent, value):
    if agent is None:
        agent = -1
    print("\nUpdate!", n_clicks, value, agent)
    plt = simulator.simulate_next_step(agent)
    for _ in range(value-1):
        plt = simulator.simulate_next_step(agent)
    return plt


def set_layout(plt):
    app.layout = [html.Div(
        dbc.Row(
            [
                dbc.Col(html.Div(dcc.Graph(figure=plt, id="graph")), style={'width': 'auto'}),
                dbc.Col(html.Div([
                    html.Div(html.Label("text", id="log"),
                             style={'width': 200, 'height': 500, 'margin-top': 150, 'overflow': 'auto'}),
                    html.Div(dcc.Dropdown(id='agent_choice', options=[
                        {'label': 'All', 'value': -1}] + [{'label': ag.name, 'value': ag.name} for ag in agents.values()]
                    , value=-1, style={'textAlign': 'center', 'margin-right': 15, 'width': 150})),
                    dbc.Input(id='count', value=1, type='number', style={'margin-right': 15}),
                    html.Button('Next', id='submit-next', n_clicks=0,
                                style={'margin-right': 15, 'width': 150, 'margin-top': 15})
                ], style={'display': 'inline-block'}), style={'width': 'auto'})
            ], justify="evenly", style={'display': 'inline-flex', 'width': 'auto'}
        ), style={'display': 'inline-flex', 'width': 'auto'}
    )]


# TODO: Textfeld als secondary output mit Events
set_layout(simulator.print_map(agent))
#for _ in range(100):
#    simulator.simulate_next_step(agent)

app.run(debug=True)
