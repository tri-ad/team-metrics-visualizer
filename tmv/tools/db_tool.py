import os
import sys

# TODO: move commands to flask-script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import click

# Imports needed for the tool
from database import db

# Import all structure classes
from structure.events import *  # pylint: disable=unused-wildcard-import
from structure.project import *  # pylint: disable=unused-wildcard-import
from structure.measurements import *  # pylint: disable=unused-wildcard-import
from structure.organization import *  # pylint: disable=unused-wildcard-import
from structure.results import *  # pylint: disable=unused-wildcard-import

# For THC import
from connectors.TeamHealthCheck.thc_read_questions import read_thc_questions
from connectors.TeamHealthCheck.thc_import import THCImporter

# For overtime data
from connectors.overtime.overtime_data_import import OTImporter


"""
    Actions for the command line tool.
    These functions can be included and executed in other files if needed.
    You can pass a function which will be used for output of status messages.
    output  - Pass a callable here which takes one argument (the text to
                output. Can for example be `print`)
"""


def action_import_teams(from_file: str, output=click.echo):
    """
    Create teams in database read from a file.

    :param from_file: The file from which to read the teams.
                      Should be row-wise with each row
                      in the format CODE|Team name
    """
    teams = []

    # Read file line-by-line and extract teams
    output(f"Reading file {from_file}...")
    try:
        with open(from_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split("|")
                teams.append(Team(code=parts[0], name=parts[1]))

                output(f"Created team {teams[-1]}.")
    except FileNotFoundError:
        output(f"File {from_file} was not found.")

    # Add to session & commit
    output(f"Adding {len(teams)} team(s) to database...")
    db.session.add_all(teams)
    db.session.commit()

    output("Done.")


def action_delete_all_for_model(model_name: str, output=click.echo) -> bool:
    """
    Remove all items for a model from the database.
    """
    output(f"Deleting all items for model {model_name} from database...")
    model_map = {
        "Team": Team,
        "OTMeasurement": OTMeasurement,
        "THCMeasurement": THCMeasurement,
        "BurndownMeasurement": BurndownMeasurement,
    }
    try:
        nr_deleted = db.session.query(model_map[model_name]).delete()
    except KeyError:
        output(f"Could not delete. Model {model_name} is not supported.")
        return False
    else:
        db.session.commit()
        output(f"{nr_deleted} records deleted.")
        return True


def action_import_thc_questions(from_file: str, output=click.echo):
    """
    Import questions for team health check from a text-file.

    :param from_file: The path to the file to read from.
                      Should be tab-separated, no header. Order
                      of columns: topic, green, red
    """
    thc_questions = []
    output(f"Reading questions from file {from_file}...")
    try:
        for q in read_thc_questions(from_file):
            thc_questions.append(
                THCQuestion(
                    deck="Basic",
                    topic=q["topic"],
                    answer_green=q["answer_green"],
                    answer_red=q["answer_red"],
                )
            )
    except FileNotFoundError:
        output(f"Error: File {from_file} does not exist!")
    else:
        # Write to session & commit
        output(f"Writing {len(thc_questions)} question(s) to database...")
        db.session.add_all(thc_questions)
        db.session.commit()
        output("Done.")


def action_process_overtime_data(
    from_file: str,
    output=click.echo,
    show_status: bool = True,
    importer_class=OTImporter,
) -> OTImporter:
    """
    Processes overtime data in a spreadsheet and returns the
    importer-instance.

    :param from_file: The path to the file to read from.
                      Should be an Excel-file with structure as described
                      in OTImporter / the sample-file in test/
    :return: OTImporter instance
    """
    with db.session.no_autoflush:  # for showing .status()
        output(f"Reading Overtime data from file {from_file}...")
        db.session.flush()
        with open(from_file, "rb") as fp:
            importer = importer_class(file=fp)
        importer.process()

        if show_status:
            output("Importer status:")
            output(importer.status())

        return importer


def action_commit_overtime_data(importer: OTImporter, output=click.echo):
    """
    Commits Overtime data read from a file to the database

    :param importer: The instance of the importer used to process the file
    """
    output("Writing to database...")
    try:
        importer.commit()
        output("Done.")
    except AttributeError as e:
        output(
            f"Error: Could not commit to database."
            f"Importer is maybe invalid or there was an internal error."
            f" Importer type is {type(importer)}."
            f" Error was: {e}."
        )


def action_process_thc(
    from_file: str, output=click.echo, show_status: bool = True
) -> THCImporter:
    """
    Imports data for Team Health Check from a spreadsheet and returns
    the importer-instance.

    :param from_file: The path to the file to read from.
        See test/resources/thc_result_test_data.xlsx for an example.
    :return: THCImporter instance
    """
    with db.session.no_autoflush:  # for showing .status()
        output(f"Reading team-health-check-data from file {from_file}...")
        db.session.flush()
        importer = THCImporter(file=from_file)
        importer.process()

        if show_status:
            output("Importer status:")
            output(importer.status())

        return importer


def action_commit_thc(importer: THCImporter, output=click.echo):
    """
    Commits Team Health Check data in an `importer` to the database.
    :param importer: The instance of the importer used to process the data
    """
    output("Writing team-health-check-data to database...")
    try:
        importer.commit()
        output("Done.")
    except AttributeError as e:
        output(
            f"Error: Could not commit to database."
            f"Importer is maybe invalid or there was an internal error."
            f" Importer type is {type(importer)}."
            f" Error was: {e}."
        )


"""
    CLI interface
    The functions below define the CLI interface. The actions actually
    performed by executing them should be defined above in the action_()-
    functions.
"""


@click.group()
def database_tool():
    pass


""" Command: Import teams from file to database """


@database_tool.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, readable=True),
    required=True,
    help=(
        "File which contains list of teams."
        "Should have one team per row and each row"
        " in the format Team code | Team name."
    ),
)
def import_teams(file: click.Path):
    action_import_teams(file)


""" Command: Delete all teams from database """


@database_tool.command()
@click.option(
    "--model",
    "-m",
    required=True,
    help=(
        "Specify the model for which you want to remove all data. "
        "Currently supported: "
        "Team, OTMeasurement, THCMeasurement, BurndownMeasurement."
    ),
)
@click.confirmation_option(
    prompt="This will remove ALL items from the given model. Are you sure?"
)
def delete_all(model):
    action_delete_all_for_model(model)


""" Command: Import THC questions from file to database """


@database_tool.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, readable=True),
    required=True,
    help=(
        "File which contains list of THC questions."
        "Should be tab separated, no header. Order of "
        "columns: topic, green, red."
    ),
)
def import_thc_questions(file: click.Path):
    action_import_thc_questions(file)


""" Command: Import overtime data from file to database """


@database_tool.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, readable=True),
    required=True,
    help=(
        "File which contains overtime worktime data."
        "Should be an appropriately formatted Excel-file. "
        "Look in test/ for an example."
    ),
)
def import_overtime_data(file: click.Path):
    importer = action_process_overtime_data(from_file=file, show_status=True)

    if click.confirm("Do you want to commit the changes to the database?"):
        action_commit_overtime_data(importer)


""" Command: Import THC data from file to database """


@database_tool.command()
@click.option(
    "--file",
    "-f",
    type=click.Path(exists=True, file_okay=True, readable=True),
    required=True,
    help=(
        "File which contains team-health-check-data."
        "Should be an appropriately formatted Excel-file. "
        "Look in test/resources for an example."
    ),
)
def import_thc_data(file: click.Path):
    importer = action_process_thc(from_file=file, show_status=True)

    if click.confirm("Do you want to commit the changes to the database?"):
        action_commit_overtime_data(importer)


""" Execute the tool """
if __name__ == "__main__":
    from app import create_app

    app = create_app()

    with app.app_context():
        database_tool()
