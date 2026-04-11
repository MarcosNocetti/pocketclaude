import os
import tempfile
import pytest
import file_manager


def test_list_dir_returns_entries(tmp_path):
    (tmp_path / "arquivo.txt").write_text("x")
    (tmp_path / "pasta").mkdir()
    result = file_manager.list_dir(str(tmp_path))
    assert "📁 pasta" in result
    assert "📄 arquivo.txt" in result


def test_list_dir_empty(tmp_path):
    assert file_manager.list_dir(str(tmp_path)) == "(empty)"


def test_list_dir_not_found():
    result = file_manager.list_dir("/caminho/que/nao/existe/xyz")
    assert "não encontrado" in result


def test_resolve_send_path_ok(tmp_path):
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"x" * 100)
    path, error = file_manager.resolve_send_path(str(f))
    assert path == str(f)
    assert error is None


def test_resolve_send_path_not_found():
    path, error = file_manager.resolve_send_path("/nao/existe/arquivo.txt")
    assert path is None
    assert "não encontrado" in error


def test_resolve_send_path_is_directory(tmp_path):
    path, error = file_manager.resolve_send_path(str(tmp_path))
    assert path is None
    assert "Não é um arquivo" in error


def test_upload_destination_creates_dir(tmp_path):
    file_manager.set_upload_dir(str(tmp_path / "uploads"))
    dest = file_manager.upload_destination("foto.jpg")
    assert dest.endswith("foto.jpg")
    assert os.path.isdir(str(tmp_path / "uploads"))
