import logging
from typing import Optional
from connectors.shared import FileImporter, ImporterReasonForSkip
from database import db
import pandas as pd
import numpy as np
from math import floor
from structure.organization import Team
from structure.measurements import THCQuestion, THCMeasurement


class THCImporter(FileImporter):
    def __init__(self, file_name):
        super().__init__(file_name, sheet_name=0, header=0, index_col=(0, 1, 2))

        # Stores questions by topic
        self._q_topics = None
        self._questions = dict()

    def get_question(self, q_topic: str) -> Optional[THCQuestion]:
        """
        Retrieve a THCQuestion-object from cache by topic.
        If not in cache, request from database.
        If not in database, return None.
        """
        try:
            return self._questions[q_topic]
        except KeyError:
            # Question was not found, so let's try to find it in the DB.
            question = (
                db.session.query(THCQuestion)
                .filter(THCQuestion.topic == q_topic)
                .first()
            )
            if question is not None:
                self._questions[q_topic] = question
            else:
                logging.warning(
                    f"Warning: Question with topic {q_topic} was "
                    "not found in database!"
                )

            # Returns None, if question was not found
            return question

    def process_header(self):
        """ Extract THC-questions from the columns of the dataframe """
        try:
            self._q_topics = self._df.columns[0::3]
        except:
            return False
        else:
            return True

    def __process_result(
        self,
        result_set: pd.Series,
        team: Team,
        question: THCQuestion,
        measurement_date,
        session_name: str,
    ):
        """ Add a result of THC to the database session """
        if any(pd.isna(result_set[:3])):
            return

        # Create measurement-object
        m = THCMeasurement(
            measurement_date=measurement_date,
            session_name=session_name,
            team=team,
            question=question,
            result_red=result_set[0],
            result_yellow=result_set[1],
            result_green=result_set[2],
        )

        # Add to session
        db.session.add(m)

    def process_row(self, index, row: pd.Series):
        """ Process one row in the dataset and add it to the database """
        if any(pd.isna([*index])):
            self.log_row_skipped(index, row, ImporterReasonForSkip.IndexWasNaN)
            return

        # Extract team-name, measurement date and session from index
        team_name = index[0]
        team = self.get_team_by_name(team_name)
        # Skip rows with unknown team
        if team is None:
            self.log_row_skipped(index, row, ImporterReasonForSkip.TeamNotFound)
            return

        # Extract measurement date and session name
        measurement_date = index[1]
        session_name = index[2]

        # Process all question topics
        i = 0
        for q_topic in self._q_topics:
            # Retrieve question
            question = self.get_question(q_topic)
            # Skip entries with unknown question
            if question is None:
                continue

            self.__process_result(
                row[i * 3 : i * 3 + 3], team, question, measurement_date, session_name
            )
            i = i + 1

    def process_final(self):
        pass
