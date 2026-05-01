import io
import os
import pytest
from unittest.mock import MagicMock, patch, call

from main import (
    get_xlsx_file,
    close_xlsx_file,
    connector,
    make_row_and_add_oldval,
    get_opslag,
    boliga_spider,
    MONTHS_DA,
    HEADERS,
)


# ---------------------------------------------------------------------------
# get_xlsx_file / close_xlsx_file
# ---------------------------------------------------------------------------

class TestGetXlsxFile:
    def test_returns_sheet_and_book(self, tmp_path):
        path = str(tmp_path / "test.xlsx")
        sheet, book = get_xlsx_file(path)
        assert sheet is not None
        assert book is not None
        book.close()

    def test_default_filename_contains_xlsxbook(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        sheet, book = get_xlsx_file()
        filename = book.filename
        assert "xlsxbook-" in filename
        book.close()

    def test_custom_filename_used(self, tmp_path):
        path = str(tmp_path / "custom.xlsx")
        sheet, book = get_xlsx_file(path)
        assert book.filename == path
        book.close()


class TestCloseXlsxFile:
    def test_closes_book(self, tmp_path):
        path = str(tmp_path / "close_test.xlsx")
        sheet, book = get_xlsx_file(path)
        close_xlsx_file(book)
        assert os.path.exists(path)

    def test_close_via_mock(self):
        mock_book = MagicMock()
        close_xlsx_file(mock_book)
        mock_book.close.assert_called_once()


# ---------------------------------------------------------------------------
# connector
# ---------------------------------------------------------------------------

class TestConnector:
    def test_calls_requests_get_with_url(self):
        mock_response = MagicMock()
        with patch("main.requests.get", return_value=mock_response) as mock_get:
            result = connector("http://example.com")
            mock_get.assert_called_once_with("http://example.com", headers=HEADERS, timeout=(5.0, 30.0))
            assert result is mock_response

    def test_uses_custom_headers(self):
        custom_headers = {"User-agent": "TestBot/1.0"}
        with patch("main.requests.get") as mock_get:
            connector("http://example.com", headers=custom_headers)
            mock_get.assert_called_once_with("http://example.com", headers=custom_headers, timeout=(5.0, 30.0))

    def test_default_headers_contain_user_agent(self):
        assert "User-agent" in HEADERS


# ---------------------------------------------------------------------------
# make_row_and_add_oldval
# ---------------------------------------------------------------------------

class TestMakeRowAndAddOldval:
    def test_writes_oldval_and_prisogtype(self):
        sheet = MagicMock()
        result = make_row_and_add_oldval(0, 1, "oldvalue", "newvalue", sheet)
        sheet.write.assert_any_call(0, 1, "oldvalue")
        sheet.write.assert_any_call(0, 2, "newvalue")
        assert result == 2

    def test_returns_incremented_columncount(self):
        sheet = MagicMock()
        result = make_row_and_add_oldval(5, 3, "a", "b", sheet)
        assert result == 4

    def test_handles_unicode(self):
        sheet = MagicMock()
        make_row_and_add_oldval(0, 0, "Prisændring", "Solgt: Alm.", sheet)
        sheet.write.assert_any_call(0, 0, "Prisændring")
        sheet.write.assert_any_call(0, 1, "Solgt: Alm.")


# ---------------------------------------------------------------------------
# get_opslag
# ---------------------------------------------------------------------------

def _html_with_opslag(h4_texts, h6_texts=None):
    h4_tags = "".join(f"<h4>{t}</h4>" for t in h4_texts)
    h6_tags = "".join(f"<h6>{t}</h6>" for t in (h6_texts or []))
    return f"""
    <html><body>
      <div class="row row-1 rowLine">
        {h4_tags}
        {h6_tags}
      </div>
    </body></html>
    """.encode("utf-8")


class TestGetOpslag:
    def test_returns_rowcount_unchanged_when_no_month_found(self):
        sheet = MagicMock()
        html = _html_with_opslag(["Noget uden måned", "Andet"])
        result = get_opslag(html, "Title", sheet, rowcount=0)
        assert result == 0
        sheet.write.assert_not_called()

    def test_increments_rowcount_when_month_found(self):
        sheet = MagicMock()
        html = _html_with_opslag(["jan", "Solgt: Alm. noget"])
        result = get_opslag(html, "MyTitle", sheet, rowcount=0)
        assert result == 1

    def test_writes_title_in_first_column_after_month(self):
        sheet = MagicMock()
        html = _html_with_opslag(["feb", "Solgt: Alm. noget"])
        get_opslag(html, "TestTitle", sheet, rowcount=2)
        sheet.write.assert_any_call(2, 0, "TestTitle")

    def test_solgt_alm_triggers_make_row(self):
        sheet = MagicMock()
        html = _html_with_opslag(["mar", "Solgt: Alm. 2.000.000"])
        get_opslag(html, "T", sheet, rowcount=0)
        calls = [str(c) for c in sheet.write.call_args_list]
        assert any("Solgt: Alm." in c for c in calls)

    def test_solgt_ukendt_triggers_make_row(self):
        sheet = MagicMock()
        html = _html_with_opslag(["apr", "Solgt: Ukendt"])
        get_opslag(html, "T", sheet, rowcount=0)
        calls = [str(c) for c in sheet.write.call_args_list]
        assert any("Solgt: Ukendt" in c for c in calls)

    def test_h6_liggetid_is_written(self):
        sheet = MagicMock()
        html = _html_with_opslag(["maj"], h6_texts=["42 dage"])
        get_opslag(html, "T", sheet, rowcount=0)
        calls = [str(c) for c in sheet.write.call_args_list]
        assert any("42 dage" in c for c in calls)

    def test_rowcount_starts_from_offset(self):
        sheet = MagicMock()
        html = _html_with_opslag(["jun", "Info"])
        result = get_opslag(html, "T", sheet, rowcount=10)
        assert result == 11
        sheet.write.assert_any_call(10, 0, "T")

    def test_no_divs_returns_same_rowcount(self):
        sheet = MagicMock()
        html = b"<html><body><p>nothing</p></body></html>"
        result = get_opslag(html, "T", sheet, rowcount=5)
        assert result == 5


# ---------------------------------------------------------------------------
# boliga_spider
# ---------------------------------------------------------------------------

class TestBoligaSpider:
    def _make_mock_response(self, page_num):
        mock = MagicMock()
        mock.content = f"<html><body><title>Bolig {page_num}</title></body></html>".encode()
        return mock

    def test_calls_connector_for_each_page(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        responses = [self._make_mock_response(i) for i in range(1, 4)]
        with patch("main.connector", side_effect=responses) as mock_conn:
            boliga_spider(3)
            assert mock_conn.call_count == 3
            mock_conn.assert_any_call("http://www.boliga.dk/bolig/1")
            mock_conn.assert_any_call("http://www.boliga.dk/bolig/2")
            mock_conn.assert_any_call("http://www.boliga.dk/bolig/3")

    def test_creates_and_closes_xlsx(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("main.connector", return_value=self._make_mock_response(1)):
            with patch("main.get_xlsx_file", wraps=get_xlsx_file) as mock_get, \
                 patch("main.close_xlsx_file", wraps=close_xlsx_file) as mock_close:
                boliga_spider(1)
                assert mock_get.call_count >= 1
                assert mock_close.call_count >= 1

    def test_handles_connector_exception_gracefully(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        with patch("main.connector", side_effect=Exception("network error")):
            boliga_spider(2)
        captured = capsys.readouterr()
        assert "network error" in captured.out

    def test_xlsx_file_created_on_disk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("main.connector", return_value=self._make_mock_response(1)):
            boliga_spider(1)
        xlsx_files = list(tmp_path.glob("xlsxbook-*.xlsx"))
        assert len(xlsx_files) == 1

    def test_rolls_over_xlsx_when_row_limit_exceeded(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        call_count = 0

        def fake_get_opslag(plain_txt, title, xlsxsheet, rowcount=0):
            nonlocal call_count
            call_count += 1
            return rowcount + 50  # always exceed row_limit=40

        responses = [self._make_mock_response(i) for i in range(1, 4)]
        with patch("main.connector", side_effect=responses), \
             patch("main.get_opslag", side_effect=fake_get_opslag):
            boliga_spider(3, row_limit=40)

        xlsx_files = list(tmp_path.glob("xlsxbook-*.xlsx"))
        assert len(xlsx_files) > 1
