from flask import current_app, flash
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database import db
from structure.project import StatusCategory, StatusCategoryStatusMapping


def create_default_status_mappings(status_mapping_dict: dict):
    unmapped_statuses = []
    for status, status_category_str in status_mapping_dict.items():
        try:
            status_category = StatusCategory(status_category_str)
        except ValueError:
            current_app.logger.error(
                f"Unable to map status `{status}` to status category `{status_category}`: Invalid status category value"
            )
            unmapped_statuses.append(status)
            continue

        # on conflict, assume manually set so ignore
        stmt = (
            pg_insert(StatusCategoryStatusMapping)
            .values(status=status, status_category=status_category)
            .on_conflict_do_nothing()
        )
        db.session.execute(stmt)
        db.session.commit()
    current_app.logger.info(f"Loaded default status mappings: {status_mapping_dict}")
    if unmapped_statuses:
        msg = f"Unmapped statuses (need manual assignment): {unmapped_statuses}"
        flash(msg, "error")
        current_app.logger.info(msg)
    else:
        flash("All statuses successfully mapped", "success")
