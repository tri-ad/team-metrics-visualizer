import logging
from typing import List, Optional
from werkzeug.datastructures import FileStorage
from uuid import uuid4
import os.path
from flask import current_app


def allowed_file(file: FileStorage, allowed_extensions: List[str] = None) -> bool:
    """
    Checks if `file` is allowed for upload. Currently only checks the file's
    extension.

    :param file: The file which was uploaded.
    :param allowed_extensions: A list of extensions which are allowed. Pass `None`
                               if you want to accept all extensions.
    :return: True if the file has an extension in `allowed_extensions`.
    """

    if allowed_extensions is None:
        return True
    else:
        _, ext = os.path.splitext(file.filename)
        return ext and ext.lstrip(".").lower() in map(str.lower, allowed_extensions)


def generate_temp_record_id() -> str:
    """ Generates a new filename for a file to be stored temporary """
    return str(uuid4())


def get_record_path(record_id: str) -> str:
    """ Returns path to a record """
    return os.path.join(current_app.config["TEMP_UPLOADS_FOLDER"], record_id)


def store_temp_file(file: FileStorage, record_id: str) -> Optional[str]:
    """
    Stores a file in the temporary storage and returns the full path to the
    file. Returns None if the process failed.

    :param file: The FileStorage-object for the file to store
    :param record_id: Filename under which to store the file
    """
    path = os.path.join(current_app.config["TEMP_UPLOADS_FOLDER"], record_id)
    try:
        file.save(path)
    except AttributeError as e:
        logging.warning("File has to be of type `FileStorage`.")
        return None
    except Exception as e:
        logging.error(f"Could not save temporary file {file} to {path}: {e}")
        return None
    else:
        return path
