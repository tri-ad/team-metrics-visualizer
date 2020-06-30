import logging
from collections import namedtuple
from typing import Dict, List, Optional, Tuple
import pandas as pd
from database import db

from flask_security import current_user
from sqlalchemy import and_, desc, func
import dash_core_components as dcc
import plotly.graph_objects as go

import tmv_dash_components as tdc
from structure.measurements import (
    THCMeasurement,
    THCQuestion,
    THCResult,
    thc_final_result,
)
from structure.organization import Team
from helpers.color import hex_to_rgb
from visuals.base import VisualController


def column_id(team_name: str, session: str) -> str:
    """
    Create a unique column ID based on team and session identifier.
    This is needed for the dash datatable.
    """
    return team_name + "_" + session


class _TeamHealthCheckVisualController:
    def final_result(self, data: pd.DataFrame) -> pd.Series:
        try:
            final_result = data.apply(
                lambda row: thc_final_result(
                    *row[["result_red", "result_yellow", "result_green"]]
                ),
                axis=1,
            )
        except KeyError as e:
            logging.error(
                "Error calculating final result of THC." f" The error was {e}."
            )
            final_result = pd.Series()
        else:
            final_result.fillna(THCResult.NoResult, inplace=True)

        return final_result


RenderInfo = namedtuple("RenderInfo", ["text", "background_color", "text_color"])


class THCResultTableController(VisualController, _TeamHealthCheckVisualController):
    """
    Visual for showing Team Health Check result in a table.
    """

    # Rendering info: text/colors.
    # Change this to change the colors in the table.
    render_info = {
        THCResult.Green: RenderInfo("Green", "tmv_green", "white"),
        THCResult.Yellow: RenderInfo("Yellow", "tmv_yellow", "white"),
        THCResult.Red: RenderInfo("Red", "tmv_red", "white"),
        THCResult.NoResult: RenderInfo("No data", "tmv_gray", "white"),
    }

    def __init__(
        self, filter_sessions: (str, str) = None, table_html_id: str = "thc_result"
    ):
        self.table_html_id = table_html_id

    def __load_data(
        self, session1: str, cmp_session: str, team_ids: Optional[List[int]] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Queries the database to retrieve team health check result for the
        teams in `team_ids` and the sessions session1 and cmp_session.
        If team_ids is None, result for all teams is retrieved.
        """
        # Set up filters for SQL-query
        if team_ids is None:
            filter_teams = True
        else:
            filter_teams = Team.team_id.in_(team_ids)

        filter_session = THCMeasurement.session_name.in_([session1, cmp_session])

        # Retrieve thc-result from database
        thc_result = pd.read_sql(
            db.session.query(
                THCMeasurement,
                Team.team_id.label("team_id"),
                Team.name.label("team_name"),
                THCQuestion.topic.label("topic"),
                THCQuestion.answer_green.label("answer_green"),
                THCQuestion.answer_red.label("answer_red"),
                THCMeasurement.session_name.label("session"),
            )
            .join(Team)
            .join(THCQuestion)
            .filter(
                and_(
                    filter_session,
                    filter_teams,
                    Team.team_id.in_(current_user.readable_team_ids),
                ),
            )
            .statement,
            db.session.bind,
        )

        # If there are no entries in the database, return an empty dataframe.
        if thc_result.empty:
            return pd.DataFrame(), {}

        # Add calculated final result of THC to dataframe
        final_result = self.final_result(thc_result)
        if final_result.empty:
            return pd.DataFrame(), {}
        else:
            thc_result.loc[:, "result"] = final_result

        thc_result_pivot = self.__pivot_table(thc_result)

        topics_data = {}
        for _i, row in thc_result.iterrows():
            topic = row["topic"]

            if topic in topics_data:
                continue

            topics_data[topic] = {
                "answer_green": row["answer_green"],
                "answer_red": row["answer_red"],
            }

        return thc_result_pivot, topics_data

    def __pivot_table(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot the thc result by session/topic in rows and team in columns.
        """
        try:
            pivot_table = data.pivot_table(
                index=["session", "topic"],
                columns=["team_name"],
                values="result",
                aggfunc=lambda x: x,
            )
        except AttributeError as e:
            logging.error(
                f"Error creating pivot table for THC result. The error was {e}."
            )
            pivot_table = pd.DataFrame()
        except ValueError as e:
            logging.error(
                "Error creating pivot table for THC result."
                f"Possibly the database is inconsistent. Error was {e}."
            )
            # TODO: This raises a ValueError: Function does not reduce in case
            # the database has non-unique entries. Can we recover from this?
            pivot_table = pd.DataFrame()
        else:
            pivot_table.fillna(THCResult.NoResult, inplace=True)

        return pivot_table

    def __table_columns(
        self, team_names: List[str], session1: str, cmp_session: str
    ) -> List:
        """
        Build list of table columns for a dash data table using the team names
        in `team_names` and the two sessions in `session1` and `cmp_session`.
        The table columns look like this for two teams and two sessions:
        Col 1       Col 2       Col 3       Col 4       Col 5
                    Team A                  Team B
        Topic       Cmp Session Session 1   Cmp Session Session 1
        """

        columns = [{"headers": [{"label": ""}, {"label": "Topic"}], "id": "topic"}]

        # If both sessions are set, create two columns per team.
        # If only one is set, create only one column per team.
        sessions = [s for s in [cmp_session, session1] if len(s) > 0]

        """ Column 2 and further: First row is team name,
            second row is session identifier """
        columns.extend(
            [
                {
                    "id": column_id(team, session),
                    "color": "#ffffff",
                    "align": "center",
                    "fontWeight": "900",
                    "headers": [
                        {"label": team, "align": "center"},
                        {"label": session, "align": "center"},
                    ],
                }
                for team in team_names
                for session in sessions
            ]
        )

        return columns

    def __table_rows(
        self,
        df: pd.DataFrame,
        topics_data: Dict[str, Dict],
        team_names: List[str],
        session1: str,
        cmp_session: str,
    ) -> List:
        """ Return correctly formatted rows for dash data table.
            The rows will be constructed using the data in `df`, for the
            teams in `team_names` and sessions `session1` and `cmp_session`.
        """

        # Return empty list if there is no data.
        if df is None or df.empty:
            return []

        # Functions to create rows and entries in the table
        def __cell(session: str, topic: str, team: str) -> str:
            """ Create a cell in the thc dash datatable
                The content of the cell is the THC-result for team `team`,
                session `session` and topic `topic`
            """
            try:
                result = df.loc[(session, topic), team]
            except KeyError:
                result = THCResult.NoResult

            if not isinstance(result, THCResult):
                return {"text": "-"}

            cell = {
                "text": self.render_info[result].text,
                "textColor": self.render_info[result].text_color,
                "backgroundColor": self.render_info[result].background_color,
            }

            # Fill trend field
            if session == session1 and result != THCResult.NoResult:
                try:
                    cmp_result = df.loc[(cmp_session, topic), team]
                except KeyError:
                    cmp_result = None

                skip_trend_field = (
                    not isinstance(cmp_result, THCResult)
                    or cmp_result == THCResult.NoResult
                    or cmp_result == result
                )
                if skip_trend_field:
                    pass  # skipping trend check if no data
                elif cmp_result > result:
                    cell["trend"] = -1
                    cell["trendTooltip"] = "Worsened"
                elif cmp_result < result:
                    cell["trend"] = 1
                    cell["trendTooltip"] = "Improved"

            return cell

        rows = []
        questions = df.index.get_level_values("topic").unique()

        for topic in questions:
            row = {
                column_id(team, session): __cell(session, topic, team)
                for session in [session1, cmp_session]
                for team in team_names
            }
            topic_data = topics_data[topic]
            row["topic"] = {
                "text": topic,
                "infoTooltip": (
                    f"Green - {topic_data['answer_green']}\n\n"
                    f"Red - {topic_data['answer_red']}"
                ),
            }
            rows.append(row)

        return rows

    def default_selection(self) -> (List[int], str, str):
        """ Return default selection for teams and sessions """
        # Retrieve most recent two sessions from database
        sessions_result = (
            db.session.query(
                THCMeasurement.session_name.label("session"),
                func.min(THCMeasurement.measurement_date).label("min_date"),
            )
            .filter(THCMeasurement.team_id.in_(current_user.readable_team_ids))
            .group_by(THCMeasurement.session_name)
            .order_by(desc("min_date"))  # Newest first, second-newest next
            .limit(2)
        )

        try:
            session1 = sessions_result[0].session
        except (IndexError, KeyError):
            session1 = ""
            logging.info("Database contains no team health check sessions")
        try:
            cmp_session = sessions_result[1].session
        except (IndexError, KeyError):
            cmp_session = ""

        # Retrieve all teams which have a THC-result
        all_teams_with_thc_result = (
            db.session.query(Team.team_id)
            .filter(Team.team_id.in_(current_user.readable_team_ids))
            .distinct()
            .join(THCMeasurement)
        )
        try:
            all_team_ids = [row[0] for row in all_teams_with_thc_result]
        except KeyError:
            logging.info("No teams with THC-result found.")
            all_team_ids = []

        return all_team_ids, session1, cmp_session

    def draw(self) -> tdc.TeamHealthTable:
        return tdc.TeamHealthTable(
            id=self.table_html_id,
            columns=[],  # filled in callback
            data=[],
            merge_duplicate_headers=True,
        )

    def update(
        self, team_ids: List[int], session1: str, cmp_session: str
    ) -> (List, pd.DataFrame):
        """
        Return columns, data and formatting for THC data table.
        Table content is built for teams in `team_ids` and sessions `session1`
        and `cmp_session`.
        """
        data, topics_data = self.__load_data(session1, cmp_session, team_ids)
        team_names = data.columns

        columns = self.__table_columns(team_names, session1, cmp_session)
        rows = self.__table_rows(data, topics_data, team_names, session1, cmp_session)

        return columns, rows


class THCTrendGraphController(VisualController, _TeamHealthCheckVisualController):

    # Graph colors
    result_colors = {
        THCResult.Red: "#fc8181",
        THCResult.Green: "#63d9a6",
        THCResult.Yellow: "#faca15",
        THCResult.NoResult: "#b3b3b3",
    }

    link_colors = {
        # adding opacity value to result_colors
        key: "rgba({}, 0.6)".format(", ".join(str(i) for i in hex_to_rgb(value)))
        for key, value in result_colors.items()
    }

    THC_RESULT_TO_ID = {THCResult.Green: 0, THCResult.Yellow: 1, THCResult.Red: 2}

    def __init__(self, graph_html_id: str = "thc_trend"):
        self.graph_html_id = graph_html_id

    def draw(self) -> dcc.Graph:
        data, layout = self.update(team_id=0)

        return dcc.Graph(
            id=self.graph_html_id, figure=go.Figure(data=data, layout=layout)
        )

    def update(self, team_id: int) -> (List[go.Sankey], Dict):
        nodes, links, err_msg = self.update_nodes_and_links(team_id=team_id)
        data = [self.sankey_graph(nodes, links)]

        layout = dict()
        # Retrieve name of selected team to show as title of the graph
        team = current_user.readable_teams.filter_by(team_id=team_id).one_or_none()

        if team:
            if len(links) > 0:
                layout["title"] = f"Trend for team {team.name}"
            else:
                layout["title"] = err_msg

        return data, layout

    def update_nodes_and_links(self, team_id: int) -> (Dict, Dict, Optional[str]):
        err_msg = None
        nodes = dict()
        links = dict()

        thc_result = self.__load_data(team_id=team_id)

        try:
            sessions = thc_result.loc[:, "session"].unique()
            questions = thc_result.loc[:, "topic"].unique()
        except KeyError:
            err_msg = (
                "Cannot draw Sankey diagram for team with id"
                f" {team_id}, because no sessions or questions"
                " were found."
            )
            logging.warning(err_msg)
        else:
            if len(sessions) < 2:
                err_msg = "Not enough sessions to draw THC Sankey-diagram."
                logging.info(err_msg)
            else:
                nodes, links = self.__sankey_nodes_and_links(
                    data=thc_result, sessions=sessions, questions=questions
                )

        return nodes, links, err_msg

    def sankey_graph(self, nodes: Dict, links: Dict) -> go.Sankey:
        nodes.update(self.__node_style())

        return go.Sankey(node=nodes, link=links, arrangement="perpendicular")

    def __node_style(self) -> Dict:
        return dict(pad=0, thickness=20, line=dict(width=0))

    def __sankey_nodes_and_links(
        self, data: pd.DataFrame, sessions, questions
    ) -> (Dict, Dict):
        """ Drawing the Sankey-diagram makes only sense, if we have >=2
            sessions (nodes columns) available. """

        # Create three nodes for each session: Green, Yellow and Red
        node_labels, node_colors = self.__sankey_nodes(sessions)
        nodes = dict(label=node_labels, color=node_colors)

        # Create links between the nodes for each result
        links_data = self.__sankey_links(
            data=data, sessions=sessions, questions=questions
        )
        link_sources, link_targets, link_values, link_labels, link_colors = links_data

        links = dict(
            source=link_sources,
            target=link_targets,
            value=link_values,
            label=link_labels,
            color=link_colors,
        )

        return nodes, links

    def __sankey_nodes(self, sessions: List[str]) -> (List, List):
        node_labels = []
        node_colors = []

        for session_i in range(len(sessions)):
            session_name = sessions[session_i]

            for result_type in (THCResult.Green, THCResult.Yellow, THCResult.Red):
                node_labels.append(f"{session_name} {result_type.name}")
                node_color = self.result_colors.get(result_type, "black")
                node_colors.append(node_color)

        return node_labels, node_colors

    def __sankey_links(  # pylint: disable=too-many-locals
        self, data: pd.DataFrame, sessions: List, questions: List
    ) -> (List, List, List, List):
        sources = []
        targets = []
        values = []
        labels = []
        colors = []

        for session_i, session_name in enumerate(sessions[:-1]):
            next_session = sessions[session_i + 1]

            source = data[data["session"] == session_name]["result"].map(
                lambda r: self.__node_id(session_i, result=r)
            )
            color = data[data["session"] == session_name]["result"].map(
                lambda r: self.link_colors.get(r, "black")
            )
            target = data[data["session"] == next_session]["result"].map(
                lambda r: self.__node_id(session_i + 1, result=r)
            )
            value = [1] * len(source)
            label = data[data["session"] == session_name]["topic"]

            sources += list(source)
            targets += list(target)
            values += list(value)
            labels += list(label)
            colors += list(color)

        return sources, targets, values, labels, colors

    def __node_id(self, session_i: int, result: THCResult) -> Optional[int]:
        number_of_result_types = len(self.THC_RESULT_TO_ID)

        try:
            result_i = self.THC_RESULT_TO_ID[result]
        except KeyError:
            logging.error(
                f"Error calculating session node for session id"
                f" {session_i} and result {result}."
            )
            return None
        else:
            return number_of_result_types * session_i + result_i

    def __load_data(self, team_id: int) -> pd.DataFrame:
        # TODO: Refactor this and avoid duplicated code with data table function
        thc_result = pd.read_sql(
            db.session.query(
                THCMeasurement,
                THCQuestion.topic.label("topic"),
                THCMeasurement.session_name.label("session"),
                Team.name.label("team_name"),
            )
            .join(Team)
            .join(THCQuestion)
            .filter(Team.team_id.in_(current_user.readable_team_ids))
            .filter(THCMeasurement.team_id == team_id)
            .order_by(THCMeasurement.measurement_date)
            .statement,
            db.session.bind,
        )

        if thc_result.empty or thc_result is None:
            return pd.DataFrame()

        # Calculate final result of each record
        final_result = self.final_result(thc_result)
        if final_result is None:
            return pd.DataFrame()

        thc_result.loc[:, "result"] = final_result

        return thc_result
