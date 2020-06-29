import logging
from typing import Optional, List
import pandas as pd
from datetime import datetime, date, timedelta

from connectors.shared import FileImporter, ImporterFileType
from connectors.shared import COL_TEAM_CODE, ImporterReasonForSkip
from database import db
from helpers.time import to_timedelta

from structure.organization import Team
from structure.measurements import OTMeasurement

COL_WORKDAYS_FIX = "Fixed Working days"
COL_WORKDAYS_ACTUAL = "Actual working days"
COL_OVERTIME = "Overtime"


class OTImporter(FileImporter):
    def __init__(self, file_name):
        # The period being processed. Parsed date from sheet_name.
        self.period = ""
        # Format for period_id
        self.period_format = "%y%m"
        """ If the Excel-file to be imported contains data for a month for
            which there is already data in the database, the importer does
            the following:
            1. Delete all the data for that month
            2. Add the new items for that month
            For this, we need to keep track of which periods are to be updated
            via uploading the file.
        """
        self.periods_affected = set()

        super().__init__(
            file_name,
            file_type=ImporterFileType.Excel,
            sheet_name=None,  # Read all sheets
            header=0,
            index_col=0,
        )

    def process_header(self) -> bool:
        # Parse sheet-name to period_id
        try:
            self.period = datetime.strptime(
                self._current_sheet, self.period_format
            ).date()
        except ValueError as e:
            self.log_sheet_skipped(
                ImporterReasonForSkip.CouldNotParseSheetName, error=e
            )
            return False

        # Check if all necessary headers are available
        if not {COL_OVERTIME, COL_WORKDAYS_ACTUAL, COL_WORKDAYS_FIX} <= set(
            self._df.columns
        ):
            logging.info(
                f"Skipping sheet {self._current_sheet}:"
                " Column headers are not complete."
                f" Column headers were: {self._df.columns}"
            )
            return False

        # Add period to affected ones to delete it before adding the new items
        self.periods_affected.add(self.period)

        # If everything's fine, return True
        return True

    def process_row(self, index, row):
        # Read team from index and retrieve from cache/db
        team_code = str(index).strip()
        team = self.get_team_by_code(team_code)

        # Skip row if team is not known
        if team is None:
            self.log_row_skipped(index, row, ImporterReasonForSkip.TeamNotFound)
            return

        # Create OT-measurement object
        m = OTMeasurement(
            measurement_date=self.period,
            team=team,
            workdays_fix=row[COL_WORKDAYS_FIX],
            workdays_actual=row[COL_WORKDAYS_ACTUAL],
            overtime=to_timedelta(row[COL_OVERTIME]),
        )

        # Add parsed measurement to list
        self.items_to_add.append(m)

    def process_final(self):
        pass

    def status(self, silent=False):
        """
        This is the custom implementation for the overtime importer.  It tells
        the user which periods will get overwritten and which ones will get
        updated.

        silent  - If set to True, the function returns the status instead
            of outputting it.

        Returns Void if silent = False and outputs the status to console
        Returns list of messages (List[str]) if silent = True
        """
        messages: List[str] = []

        messages.append(
            "Overtime data for following periods will be added" " to the database:"
        )
        for p in sorted(self.periods_affected):
            try:
                messages.append("- " + p.strftime("%Y %B"))
            except AttributeError:
                messages.append("- " + p.__repr__())

        messages.append(
            "Any existing overtime data for the periods listed"
            " above will be overwritten!"
        )

        # TODO: Add a full list of teams to this.

        # Return status or print it to the console
        if silent:
            return messages
        else:
            for m in messages:
                print(m)

    def commit(self):
        """
        Deletes all data from the database for the periods which were in the
        imported file. After that, adds the new data from the file.
        """

        """ Step 1: Delete all periods which were to be overwritten
            We use synchronize_session=False, because we don't want to delete
            the newly added records which are stored in the session """
        logging.info(
            f"Deleting overtime records from database for periods: "
            f"{[d.strftime('%Y/%m') for d in sorted(self.periods_affected)]}"
        )
        result_delete = (
            db.session.query(OTMeasurement)
            .filter(OTMeasurement.measurement_date.in_(self.periods_affected))
            .delete(synchronize_session=False)
        )
        logging.info(f"Done. Rows matched: {result_delete}")

        """ Step 2: Add all new items. We use the commit()-method of the
            base-class for this. """
        logging.info(f"Adding {len(self.items_to_add)} items to database.")
        db.session.add_all(self.items_to_add)
        super().commit()
