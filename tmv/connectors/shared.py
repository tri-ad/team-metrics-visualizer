import logging
from typing import Optional, Callable, Dict
from abc import ABC, abstractmethod
import pandas as pd
from enum import Enum, auto
import os.path
from database import db
from structure.organization import Team


class ImporterFileType(Enum):
    """ File types which can be imported using FileImporter-subclasses """

    CSV = auto()
    Excel = auto()


class ImporterReasonForSkip(Enum):
    """ Indicates reason for skipping a row during import """

    IndexWasNaN = auto()
    TeamNotFound = auto()
    CouldNotParseSheetName = auto()
    Unknown = auto()


# Column names for files with headers
COL_TEAM = "Team"
COL_TEAM_CODE = "Code"
COL_DATE = "Date"


class FileImporter(ABC):
    """
    Load a file to a dataframe.
    Abstract class to be used as base class for connectors.
    The typical use of `SomethingImporter(FileImporter)` is:

    1. Instantiate:
       `importer = SomethingImporter(database_session, "path/to/file.xlsx")`
    2. Process file: `importer.process()`
    3. (Optional, for interactive use) Show changes to DB: `importer.status()`
    4. Commit changes to database: `importer.commit()`.

    `process()` is implemented in `FileImporter` and processes the file
    header (with `process_header()`), each row (with `process_row()`) and
    then calls `process_final()` in case any final processing is needed after
    iterating through all the rows.

    The methods `process_*` are to be implemented by the subclass.
    """

    def __init__(
        self, file_name: str, file_type: Optional[ImporterFileType] = None, **kwargs
    ):
        # Data of Excel sheet is to be stored here. Dict of dataframes
        self._data: Optional[Dict[str, pd.DataFrame]] = None
        # Remember if only one sheet was read or not
        self._only_one_sheet = False
        # Name of current sheet
        self._current_sheet = ""
        # Dataframe to store the contents of one sheet while processing
        self._df: Optional[pd.DataFrame] = None

        # List for storing items to be added to the database
        self.items_to_add = []

        # Dictionary for storing teams from the DB
        self._teams_by_name = dict()
        self._teams_by_code = dict()

        # If file type is not given, try to infer from suffix
        if file_type is None:
            _, ext = os.path.splitext(file_name)
            ext = ext.lower()
            if ext == ".xlsx" or ext == ".xls":
                file_type = ImporterFileType.Excel
            elif ext == ".csv":
                file_type = ImporterFileType.CSV
            else:
                file_type = None

        # Read the file into a pandas dataframe
        if file_type == ImporterFileType.Excel:
            self.__read_file(file_name, pd.read_excel, **kwargs)
        elif file_type == ImporterFileType.CSV:
            self.__read_file(file_name, pd.read_csv, **kwargs)
        else:
            logging.warning(f"File type {file_type.name} is not supported.")

        super().__init__()

    def _get_team(self, filter_) -> Optional[Team]:
        return Team.query.filter(filter_).first()

    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Retrieve team object by name."""
        try:
            return self._teams_by_name[name]
        except KeyError:
            team = self._get_team(Team.name == name)
            self._teams_by_name[name] = team
            return team

    def get_team_by_code(self, code: str) -> Optional[Team]:
        """Retrieve team object by code."""
        try:
            return self._teams_by_code[code]
        except KeyError:
            team = self._get_team(Team.code == code)
            self._teams_by_code[code] = team
            return team

    def __read_file(
        self, file_name: str, engine: Callable[..., pd.DataFrame], **eng_kwargs
    ):
        """
        Read the file to be imported and save it in a dict of Dataframes.

        :param file_name: The path to the file
        :param engine: A function to use for reading the file.
                       Should return a pd.DataFrame.
        :param eng_kwargs: Keyword-arguments for the engine.

        Example::

            __read_file('myfile.xlsx', pd.read_excel, index_col=(0,1,2))
        """
        try:
            data = engine(file_name, **eng_kwargs)
        except FileNotFoundError as e:
            logging.error(f"File {file_name} was not found: {e}.")
            self._data = {"0": pd.DataFrame()}
            self._only_one_sheet = True
        except Exception as e:
            logging.error(f"Error reading file to dataframe: {e}.")
            self._data = {"0": pd.DataFrame()}
            self._only_one_sheet = True
        else:
            if type(data) is pd.DataFrame:
                self._data = {"0": data}
                self._only_one_sheet = True
            else:
                try:  # Try out if data is a dict-like
                    data.items()
                except:
                    raise ValueError(
                        f"Data is of type {type(data)} " "which is not supported"
                    )
                else:
                    self._data = data
                    self._only_one_sheet = False

    @abstractmethod
    def process_header(self) -> bool:
        """
        Processes header of the sheet (if there is one)
            Return False if you want to skip the current sheet
        """
        pass

    @abstractmethod
    def process_row(self, index, row: pd.Series):
        """
        Processes one row of the data frame and adds it to the DB session.
        """
        pass

    @abstractmethod
    def process_final(self):
        """ Gets called as the last step of process() """
        pass

    def log_row_skipped(self, index, row: pd.Series, reason: ImporterReasonForSkip):
        """ Shows a log message in case a row was skipped """
        if reason == ImporterReasonForSkip.IndexWasNaN:
            logging.info(
                f"A row was skipped because of the index"
                f" containing NaN values. Index was {index}."
            )
        elif reason == ImporterReasonForSkip.TeamNotFound:
            logging.info(
                "A row was skipped because the team it contains"
                f" was not found in the database. Index was {index},"
                f" row was {row}."
            )
        else:
            logging.info(
                f"A row was skipped for an unknown reason."
                f"Index was {index}, row was {row}."
            )

    def log_sheet_skipped(self, reason: ImporterReasonForSkip, error=None):
        """ Shows a log message in case a sheet was skipped """
        sheet_name = self._current_sheet

        if reason == ImporterReasonForSkip.CouldNotParseSheetName:
            logging.info(
                f"Sheet {sheet_name} was skipped because the"
                " sheet name could not be parsed."
            )
        else:
            logging.warning(f"Sheet {sheet_name} was skipped due to an unknown reason.")

        if error is not None:
            logging.error(f"The error was: {error}.")

    def process(self, interactive=False):
        """
        Process header and rows of all sheets in the file.

        :param interactive: Shows the user what will be changed
                            in the database and asks for confirmation.
        """
        # TODO: Implement interactive
        for sheet_name, df in self._data.items():
            if not self._only_one_sheet:
                logging.debug(f"Processing sheet '{sheet_name}':")
                self._current_sheet = sheet_name
            else:
                self._current_sheet = ""

            self._df = df

            # Process header
            if self.process_header():
                # Process rows
                for index, row in self._df.iterrows():
                    self.process_row(index, row)

                # Finish up
                self.process_final()

        # TODO: Log changes

    def status(self, silent=False):
        """
        Show session status

        :param silent: If set to True, the function returns the status instead
                       of outputting it.

        :return: Returns Void if silent = False and outputs the status to console
                 Returns list of messages (List[str]) if silent = True
        """
        messages = []

        if db.session.autoflush:
            messages.append(
                "WARNING: Autoflush is enabled in the database session."
                " The list below will therefore not show all items."
                " You should deactivate autoflush in order for status()"
                " to work properly."
            )

        # Set titles for status print
        titles = [
            "Following items will be ADDED to the database:",
            "Following items will be MODIFIED:",
            "Following items will be DELETED:",
        ]
        # Check all objects to be added, updated and deleted
        objects = [
            [x for x in session_set]
            for session_set in [db.session.new, db.session.dirty, db.session.deleted]
        ]

        # Flush session to get IDs
        db.session.flush()

        # Show list of objects
        for t, o in zip(titles, objects):
            messages.append(t)
            [messages.append(x.__repr__()) for x in o]

        # Return status or print it to the console
        if silent:
            return messages
        else:
            for m in messages:
                print(m)

    def commit(self):
        """ Commit the processed rows to the database """
        db.session.commit()

    def rollback(self):
        """ Roll back the changes """
        db.session.rollback()
