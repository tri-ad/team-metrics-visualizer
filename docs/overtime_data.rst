Overtime Data
=============

Overtime Data is shown as part of the visuals for Team Health.


Uploading Data
--------------

Overtime Data is filled via import in the admin pages.

A specific format is required for the uploaded file as detailed below. Sample data is available for download :download:`here <../tmv/static/admin/overtime_sample_data.xlsx>`.


File Format Specifications
**************************

1. File Type: `.xlsx` or `.xls`
2. Sheet Names: Year and month in `YYMM` format meaning each sheet corresponds to a specific month and year.
3. Columns

   +-------------+-------------------------------------------------------------+
   | Column Name | Description                                                 |
   +=============+=============================================================+
   | Code        | *Required as first column*. Team code uniquely identifying  |
   |             | the team. Maps to Team model's code field.                  |
   |             | See :ref:`organization-module`                              |
   +-------------+-------------------------------------------------------------+
   | Overtime    | *Required*. Total time of overtime in `hours:minutes`       |
   |             | format for team represented by `Code`.                      |
   +-------------+-------------------------------------------------------------+
   | Fixed       | *Required*. Number of working days in the month.            |
   | Working     |                                                             |
   | days        |                                                             |
   +-------------+-------------------------------------------------------------+
   | Actual      | *Required*. Number of actual days worked in the month.      |
   | working     |                                                             |
   | days        |                                                             |
   +-------------+-------------------------------------------------------------+
