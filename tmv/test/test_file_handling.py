import pytest
from file_handling.helpers import allowed_file
from werkzeug.datastructures import FileStorage


def test_allowed_files_all_extensions_ok():
    """ Test if disabled file extension check works """
    assert allowed_file(FileStorage(filename="yup!"))
    assert allowed_file(FileStorage(filename="yup."))
    assert allowed_file(FileStorage(filename="yup.xlsx"))
    assert allowed_file(FileStorage(filename="yup.EXE"))


def test_allowed_files_no_extensions_ok():
    """ Test if file extension check works for no allowed files """
    assert not allowed_file(FileStorage(filename="nope"), allowed_extensions=[])
    assert not allowed_file(FileStorage(filename="nope.xlsx"), allowed_extensions=[])
    assert not allowed_file(FileStorage(filename="nope.csv"), allowed_extensions=[])
    assert not allowed_file(FileStorage(filename="nope."), allowed_extensions=[])
    assert not allowed_file(
        FileStorage(filename="a/b.nope/c.pptx"), allowed_extensions=[]
    )


def test_allowed_files_excel_files():
    """ Test if file extension check works properly """
    ae = ["xlsx", "xls"]

    assert allowed_file(FileStorage(filename="ok.xlsx"), allowed_extensions=ae)
    assert allowed_file(FileStorage(filename="ok.XLSX"), allowed_extensions=ae)
    assert allowed_file(FileStorage(filename="ok.xls"), allowed_extensions=ae)
    assert allowed_file(FileStorage(filename="ok.xLs"), allowed_extensions=ae)

    assert not allowed_file(FileStorage(filename="nope.pptx"), allowed_extensions=ae)
    assert not allowed_file(FileStorage(filename="nope.xlsxs"), allowed_extensions=ae)
    assert not allowed_file(FileStorage(filename="nope.EXE"), allowed_extensions=ae)
    assert not allowed_file(FileStorage(filename="nope."), allowed_extensions=ae)
    assert not allowed_file(FileStorage(filename="nope"), allowed_extensions=ae)
    assert not allowed_file(
        FileStorage(filename="a/b.xlsx/nope"), allowed_extensions=ae
    )
    assert not allowed_file(FileStorage(filename="a/b.exe/nope"), allowed_extensions=ae)
