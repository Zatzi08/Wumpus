from Project.Environment.env import EnvGenerator
from Project.Environment.TileCondition import TileCondition
#from Project.SimulatedAgent import SimulatedAgent

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from numpy.dtypes import StringDType
import numpy as np


class Map:
    __slots__ = ['height', 'width', 'start_pos', 'map', 'filled_map', 'agents', 'info']

    def __init__(self, width, height):
        # extend grid to fit full tiles
        self.height = height
        self.width = width

        if width % 3 != 0:
            self.width += 3 - (width % 3)
        if height % 3 != 0:
            self.height += 3 - (height % 3)

        self.start_pos = (1, 1)
        gen = EnvGenerator(self.height, self.width)
        self.map = gen.getGrid()
        gen.placeWorldItems()
        self.filled_map = gen.getGrid()
        self.agents = {}
        self.info = gen.get_map_info()

    def add_agents(self, agents):
        self.agents = agents

    def get_tile_conditions(self, x, y):
        return self.filled_map[y][x]

    def __get_neighbors_of(self, x: int, y: int) -> list[tuple[int, int]]:
        adjacent: list[tuple[int, int]] = []
        for (xi, yi) in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if TileCondition.WALL in self.filled_map[y + yi][x + xi]:
                continue
            adjacent.append((x, y))
        return adjacent

    def get_agents_in_reach(self, name: int, distance: int) -> list[int]:
        agent = self.agents[name]

        # find adjacent tiles (reachable in [distance] moves)
        x: int = agent.position[0]
        y: int = agent.position[1]
        adjacent_tiles: set[tuple[int, int]] = {(x, y)}
        current_tiles_1: set[tuple[int, int]] = {(x, y)}
        current_tiles_2: set[tuple[int, int]] = set(self.__get_neighbors_of(x, y))
        if distance <= 0:
            pass
        elif distance == 1:
            adjacent_tiles.update(current_tiles_2)
        elif distance > 1:
            adjacent_tiles.update(current_tiles_2)
            i: int = 1
            relay: bool = True
            while i < distance:
                if relay:
                    current_tiles_1.clear()
                    for (x, y) in current_tiles_2:
                        current_tiles_1.update(self.__get_neighbors_of(x, y))
                    relay = False
                    adjacent_tiles.update(current_tiles_1)
                else:
                    current_tiles_2.clear()
                    for (x, y) in current_tiles_1:
                        current_tiles_2.update(self.__get_neighbors_of(x, y))
                    relay = True
                    adjacent_tiles.update(current_tiles_2)
                i += 1

        # find adjacent agents (on adjacent tiles)
        adjacent_agents = []
        for agent in self.agents.values():
            if agent.name == name:
                continue
            if agent.position in adjacent_tiles:
                adjacent_agents.append(agent.name)
        return adjacent_agents

    def delete_condition(self, x, y, condition: TileCondition):
        self.filled_map[y][x].remove(condition)
        if condition in [TileCondition.WUMPUS, TileCondition.PIT]:
            self.filled_map[y][x].append(TileCondition.SAFE)
            if condition == TileCondition.WUMPUS:
                second_condition = TileCondition.STENCH
            else:
                second_condition = TileCondition.BREEZE
            for ox, oy in [(0, 1), (-1, 0), (0, -1), (1, 0)]:
                self.__delete_stench_or_breeze(x + ox, y + oy, second_condition)

    def __delete_stench_or_breeze(self, x, y, condition: TileCondition):
        if condition != TileCondition.STENCH:
            raise "Invalid Condition"
        cond = self.get_tile_conditions(x, y)
        if condition not in cond:
            #print("Incorrect Map Initialization - eventual Error in Map line 107")
            return
        self.filled_map[y][x].remove(TileCondition.STENCH)


    def get_safe_tiles(self):
        return sorted(self.info[TileCondition.SAFE.value])

    def __print_base(self, grid):
        def convertGrid(grid):
            g = np.ndarray((self.height, self.width), float)
            b = np.ndarray((self.height, self.width), dtype=StringDType())

            for y in range(0, self.height):
                for x in range(0, self.width):
                    if TileCondition.WALL in list(grid[y][x]):
                        g[y][x] = 0.05
                        b[y][x] = "Wall"
                    elif TileCondition.WUMPUS in list(grid[y][x]):
                        g[y][x] = 0.2
                        b[y][x] = "Wumpus"
                    elif TileCondition.SHINY in list(grid[y][x]):
                        g[y][x] = 0.3
                        b[y][x] = "Gold"
                    elif TileCondition.PIT in list(grid[y][x]):
                        g[y][x] = 0.4
                        b[y][x] = "Pit"
                    elif TileCondition.PREDICTED_WUMPUS in list(grid[y][x]):
                        g[y][x] = 0.5
                        b[y][x] = "Predicted Wumpus"
                    elif TileCondition.PREDICTED_PIT in list(grid[y][x]):
                        g[y][x] = 0.6
                        b[y][x] = "Predicted Pit"
                    elif TileCondition.BREEZE in list(grid[y][x]) and TileCondition.STENCH in list(grid[y][x]):
                        g[y][x] = 0.7
                        b[y][x] = "Breeze and Stench"
                    elif TileCondition.BREEZE in list(grid[y][x]):
                        g[y][x] = 0.8
                        b[y][x] = "Breeze"
                    elif TileCondition.STENCH in list(grid[y][x]):
                        g[y][x] = 0.9
                        b[y][x] = "Stench"
                    elif TileCondition.SAFE in list(grid[y][x]):
                        g[y][x] = 1.0
                        b[y][x] = "Path"
                    else:
                        g[y][x] = 0.1
                        b[y][x] = 'Unknown'

            return g, b

        data, txt = convertGrid(grid)

        plt = make_subplots(specs=[[{"secondary_y": True}]])

        cmap = [[0., 'black'], [0.05, 'black'], [0.05, 'grey'], [0.1, 'grey'], [0.1, 'darkred'], [0.2, 'darkred'],
                [0.2, 'yellow'], [0.3, 'yellow'], [0.3, 'blue'], [0.4, 'blue'], [0.4, 'red'], [0.5, 'red'],
                [0.5, 'turquoise'], [0.6, 'turquoise'], [0.6, 'green'], [0.7, 'green'], [0.7, 'lightblue'],
                [0.8, 'lightblue'],
                [0.8, 'lightgreen'], [0.9, 'lightgreen'], [0.9, 'white'], [1., 'white']]
        plt.add_trace(go.Heatmap(name="",
                                 z=data,
                                 text=txt,
                                 colorscale=cmap,
                                 showscale=False,
                                 hovertemplate="<br> x: %{x} <br> y: %{y} <br> %{text}"), )
        plt.update_layout(dict(autosize=False, width=840, height=840))

        return plt

    def print_map(self):

        """
        @author: Lucas K
        @:return plotly
        """

        plt = self.__print_base(self.filled_map)
        position = dict()
        for a in self.agents.values():
            position[a.position] = f"{position.get(a.position, "")}{a.name} : {a.role.name}<br>"
        xs = []
        ys = []
        ag = []
        for key in position.keys():
            x, y = key
            xs.append(x)
            ys.append(y)
            ag.append(position[key])

        plt.add_trace(go.Scatter(
            mode="markers",
            x=xs,
            y=ys,
            text=ag,
            hovertemplate="%{text}",
            name=""
        ))

        plt.update_xaxes(dict(fixedrange=True, showgrid=False))
        plt.update_yaxes(dict(fixedrange=True, showgrid=False, showline=True))

        plt.update_layout(dict(autosize=False, width=840, height=840))

        return plt


def print_agent_map(grid, width, height, agent):
    def convertGrid(grid):
        g = np.ndarray((height, width), float)
        b = np.ndarray((height, width), dtype=StringDType())

        for y in range(0, height):
            for x in range(0, width):
                if TileCondition.WALL in list(grid[y][x]):
                    g[y][x] = 0.05
                    b[y][x] = "Wall"
                elif TileCondition.WUMPUS in list(grid[y][x]):
                    g[y][x] = 0.2
                    b[y][x] = "Wumpus"
                elif TileCondition.SHINY in list(grid[y][x]):
                    g[y][x] = 0.3
                    b[y][x] = "Gold"
                elif TileCondition.PIT in list(grid[y][x]):
                    g[y][x] = 0.4
                    b[y][x] = "Pit"
                elif TileCondition.PREDICTED_WUMPUS in list(grid[y][x]):
                    g[y][x] = 0.5
                    b[y][x] = "Predicted Wumpus"
                elif TileCondition.PREDICTED_PIT in list(grid[y][x]):
                    g[y][x] = 0.6
                    b[y][x] = "Predicted Pit"
                elif TileCondition.BREEZE in list(grid[y][x]) and TileCondition.STENCH in list(grid[y][x]):
                    g[y][x] = 0.7
                    b[y][x] = "Breeze and Stench"
                elif TileCondition.BREEZE in list(grid[y][x]):
                    g[y][x] = 0.8
                    b[y][x] = "Breeze"
                elif TileCondition.STENCH in list(grid[y][x]):
                    g[y][x] = 0.9
                    b[y][x] = "Stench"
                elif TileCondition.SAFE in list(grid[y][x]):
                    g[y][x] = 1.0
                    b[y][x] = "Path"
                else:
                    g[y][x] = 0.1
                    b[y][x] = 'Unknown'

        return g, b

    data, txt = convertGrid(grid)

    plt = make_subplots(specs=[[{"secondary_y": True}]])

    cmap = [[0., 'black'], [0.05, 'black'], [0.05, 'grey'], [0.1, 'grey'], [0.1, 'darkred'], [0.2, 'darkred'],
            [0.2, 'yellow'], [0.3, 'yellow'], [0.3, 'blue'], [0.4, 'blue'], [0.4, 'magenta'], [0.5, 'magenta'],
            [0.5, 'turquoise'], [0.6, 'turquoise'], [0.6, 'green'], [0.7, 'green'], [0.7, 'lightblue'],
            [0.8, 'lightblue'],
            [0.8, 'lightgreen'], [0.9, 'lightgreen'], [0.9, 'white'], [1., 'white']]
    plt.add_trace(go.Heatmap(name="",
                             z=data,
                             text=txt,
                             colorscale=cmap,
                             showscale=False,
                             hovertemplate="<br> x: %{x} <br> y: %{y} <br> %{text}"), )

    plt.add_trace(go.Scatter(
        mode="markers",
        x=[agent.position[0]],
        y=[agent.position[1]],
        text=[f"{agent.name} : {agent.role.name}"],
        hovertemplate="%{text}",
        name=""
    ))

    plt.update_xaxes(dict(fixedrange=True, showgrid=False))
    plt.update_yaxes(dict(fixedrange=True, showgrid=False, showline=True))

    plt.update_layout(dict(autosize=False, width=840, height=840))

    return plt
