from dash import dcc, Dash, html, Input, Output, State, callback
import dash_bootstrap_components as dbc

from Project.SimulatedAgent.AgentEnums import AgentGoal
from Project.Simulator import Simulator

app = Dash()
agent = -1
templateHead = '{:10s} {:15s} {:15s} {:15s}'
template = '{:>20s} {:>20s} {:>20s} {:>20s}\n'

simulator = Simulator(60, 60, 10, 200, seed=140, with_communication=False)
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
    plt, meta = simulator.simulate_next_step(agent)     # meta: list[list[tuple[int, bool]]]
    s = ""
    for _ in range(value - 1):
        plt, meta = simulator.simulate_next_step(agent)
    for agentName in range(len(meta)):
        g = ""
        w = ""
        m = ""
        for goalID in range(len(meta[agentName])):
            u = "{:s}"
            if meta[agentName][goalID][1]:
                u = "    __{:s}__"
            match goalID:
                case 0:
                    g = u.format(str(meta[agentName][goalID][0]))
                case 1:
                    w = u.format(str(meta[agentName][goalID][0]))
                case 2:
                    m = u.format(str(meta[agentName][goalID][0]))
        s += template.format(str(agentName), g, w, m)
    #for agentGoal in agentGoalList:

    return plt, s


def set_layout(plt, text):
    app.layout = html.Div(
        dbc.Row(
            [
                dbc.Col(
                    html.Div(dcc.Graph(figure=plt, id="graph"), style={'width': '100%'}),
                    width={'size': 12, 'sm': 6, 'md': 6, 'lg': 6},
                ),
                dbc.Col(
                    html.Div([
                        html.Div([
                            dcc.Markdown(templateHead.format('Name', "Gold owned", "Wumpus killed", "Map Progress"),
                                         id="junk", style={'white-space': 'pre', 'position': 'sticky', 'margin-top': 150}),
                            dcc.Markdown(children=text, id="log", style={'width': '100%', 'height': 500, 'white-space': 'pre', 'overflow': 'auto', 'margin-top': -20, 'margin-left': 30})
                        ], style={'margin-top': '20px'}),
                        html.Div(
                            dcc.Dropdown(id='agent_choice', placeholder='Select agent view', options=[{'label': 'Full Map View', 'value': -1}] + [{'label': f"Agent view: {ag.name}", 'value': ag.name} for ag in agents.values()],
                                         value=-1, style={'textAlign': 'center', 'margin-right': 15, 'width': '100%'}),
                            style={'margin-bottom': '20px'}
                        ),
                        dbc.Input(id='count', value=1, type='number',
                                  style={'width': '50%'}),
                        html.Button('Next', id='submit-next', n_clicks=0,
                                    style={'width': '46%'})
                    ], style={'display': 'inline-block', 'width': '100%', 'max-width': '600px'}),
                    width={'size': 12, 'sm': 6, 'md': 6, 'lg': 6}
                ),
            ],
            justify="center", align="center", style={'min-height': '100vh', 'display': 'flex'}
        ),
        style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}
    )

def start_layout(plt, meta):
    s = ""
    for agentName in range(len(meta)):
        g = ""
        w = ""
        m = ""
        for goalID in range(len(meta[agentName])):
            u = "{:s}"
            if meta[agentName][goalID][1]:
                u = "    __{:s}__"
                last = True
            match goalID:
                case 0:
                    g = u.format(str(meta[agentName][goalID][0]))
                case 1:
                    w = u.format(str(meta[agentName][goalID][0]))
                case 2:
                    m = u.format(str(meta[agentName][goalID][0]))
        s += template.format(str(agentName), g, w, m)
    set_layout(plt, s)

# TODO: Textfeld als secondary output mit Events
p, me = simulator.print_map(agent)
start_layout(p, me)

app.run(debug=True)
