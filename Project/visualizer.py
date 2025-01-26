from dash import dcc, Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

from Project.SimulatedAgent.AgentEnums import AgentGoal
from Project.Simulator import Simulator

app = Dash()
agent = -1
template = '{:10s} {:15s} {:15s} {:15s}\n'

simulator = Simulator(60, 60, 6, 2000)
agents = simulator.get_agents()

@callback(
    Output('graph', 'figure'),
    Output("log", "children"),
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
    s = template.format('Name', "Gold owned", "Wumpus killed", "Map Progress")
    print(s)
    for _ in range(value-1):
        plt = simulator.simulate_next_step(agent)
    #for agentGoal in agentGoalList:

    return plt, s


def set_layout(plt):
    app.layout = [html.Div(
        dbc.Row(
            [
                dbc.Col(html.Div(dcc.Graph(figure=plt, id="graph")), style={'width': 'auto'}),
                dbc.Col(html.Div([
                    html.Div(dcc.Markdown(children=template.format('Name', "Gold owned", "Wumpus killed", "Map Progress"), id="log", style={'white-space':'pre'}),
                             style={'width': 600, 'height': 500, 'margin-top': 150, 'overflow': 'auto'}),
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
