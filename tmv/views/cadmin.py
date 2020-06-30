import logging
from typing import Optional

from flask import (
    flash,
    redirect,
    request,
    send_from_directory,
    url_for,
)
from flask_security import current_user
from flask_admin import BaseView, expose

from helpers.file_handling import (
    allowed_file,
    store_temp_file,
    generate_temp_record_id,
    get_record_path,
)
from database import db  # pylint: disable=unused-import
from structure.organization import Team
from connectors.overtime.overtime_data_import import OTImporter
from tools.db_tool import action_process_overtime_data, action_commit_overtime_data


SUPPORTED_CONNECTORS = ["overtime"]
OVERTIME_SUPPORTED_EXTENSIONS = ["xlsx", "xls"]


class OTImporterAdminPage(OTImporter):
    def _get_team(self, filter_) -> Optional[Team]:
        """Return only teams user has access to."""
        have_access_to_all_data = current_user.has_role(
            "superadmin"
        ) or current_user.has_role("dataprovider")
        if have_access_to_all_data:
            return super()._get_team(filter_)

        return current_user.writable_teams.filter(filter_).first()


class UploadDataView(BaseView):
    """File upload

    File upload goes through three steps:

    1. upload() - The user can pick a file to upload
    2. upload_confirm() - The user can see the changes which will be made
       and cancel or confirm them.
    3. upload_process() - If the user confirmed in step 2, the file gets
       processed and changes commited to the database.

    TODO: Right now, the file gets processed twice: in step 2 and 3. It
    should only get processed once.

    URL arguments:

    - connector   - This specifies which connector (=system, file type) to
      use. Depending on the chosen connector, the file
      processing is different and the tool writes to
      different tables. Currently supported connectors:

      - Overtime
      - TODO: Implement import of data for Team Health Check
    - rec_id  - The ID for the temporarily stored file. This is to keep track
      of the file between the steps of the process. The
      record-ID is created in step 1 and passed to step 2 and 3.

    TODO: Currently, temp files do never get deleted. They should get deleted
    after some time.

    """

    def __init__(self, *args, **kwargs):
        self.connector = kwargs.pop("connector")

        if self.connector not in SUPPORTED_CONNECTORS:
            raise ValueError(f"connector {repr(self.connector)} is not supported")

        super().__init__(*args, **kwargs)

    def is_accessible(self):
        return (
            current_user.is_superadmin
            or current_user.has_role("dataprovider")
            or current_user.writable_teams.count()
        )

    @expose("/", methods=["GET"])
    def upload_index(self):
        """Display file upload page for the `connector`."""
        return self.render("cadmin/upload.html", connector=self.connector)

    @expose("/", methods=["POST"])
    def upload(self):
        """Save the file uploaded for the connector."""

        # Try to retrieve the file from the request
        file = None
        try:
            file = request.files["file"]
        except KeyError as e:
            logging.warning(f"File was not found in request: {e}.")
            flash("No file given.", "error")
            return redirect(request.url)
        except AttributeError as e:
            logging.warning(f"Error: Request did not contain any files: {e}.")
            flash("No file given.", "error")
            return redirect(request.url)

        # Check if file was correctly uploaded
        if not file or len(file.filename) == 0:
            flash("No file selected for upload.", "message")
            return redirect(request.url)

        """ Check if file has correct extension. Allowed extensions depend on
            the connector. To make the code more readable, group connectors
            with the same allowed file extensions together like this:
                if connector in ['someconnector', 'someotherconnector']:
                    extensions = [...] """

        if self.connector in ["overtime"]:
            allowed_extensions = OVERTIME_SUPPORTED_EXTENSIONS
        else:
            allowed_extensions = []

        if not allowed_file(file, allowed_extensions=allowed_extensions):
            flash("File extension not allowed.", "warning")
            return redirect(request.url)

        """ File seems uploaded correctly and has correct extension.
        Generate a new record ID to keep track of the uploaded file.
        """
        rec_id = generate_temp_record_id()

        # Save file to disk
        path = store_temp_file(file, record_id=rec_id)

        if not path:
            flash("Error saving file!", "error")
            return redirect(request.url)

        """ If everything ended successfully, send the user to the
        confirmation page so he can review his changes """

        return redirect(url_for(f"{self.endpoint}.upload_confirm", rec_id=rec_id))

    @expose("confirm/<rec_id>")
    def upload_confirm(self, rec_id: str):  # pylint: disable=unused-variable
        """
        Display a page showing what will be changed in the database
        after the data from a file uploaded by the user has been added.
        Ask the user for confirmation.

        :param connector: The connector to use (e.g.: THC, overtime, ...)
        :param rec_id: The record-ID of the uploaded file
        """
        # Process the uploaded file
        if self.connector == "overtime":
            importer = action_process_overtime_data(
                get_record_path(rec_id),
                output=print,
                show_status=False,
                importer_class=OTImporterAdminPage,
            )
        else:
            return "Unknown upload file type :("

        # Build string of status messages
        status = "\n".join(importer.status(silent=True))

        # Show template with status and ask for confirmation
        return self.render(
            "cadmin/upload_confirm.html",
            confirm_url=url_for(f"{self.endpoint}.upload_process", rec_id=rec_id),
            status=status,
        )

    @expose("process/<rec_id>")
    def upload_process(self, rec_id: str):  # pylint: disable=unused-variable
        """
        Actually process the uploaded file and add it to the database.

        :param connector: The connector to use (e.g.: THC, overtime, ...)
        :param rec_id: The record-ID of the uploaded file
        """

        # Process the uploaded file
        if self.connector == "overtime":
            importer = action_process_overtime_data(
                get_record_path(rec_id), output=print, show_status=True
            )
            action_commit_overtime_data(importer, output=print)
        else:
            flash("Unknown upload file type :(", "error")

        flash("Data successfully uploaded!", "info")

        return redirect(url_for(f"{self.endpoint}.upload"))

    @expose("download_sample")
    def download_sample(self):
        return send_from_directory(
            "static",
            filename="admin/overtime_sample_data.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            attachment_filename="overtime_sample_data.xlsx",
            as_attachment=True,
        )
