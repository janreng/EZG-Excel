"""Test SSL context cua updater (fix CERTIFICATE_VERIFY_FAILED). ASCII only."""
import ssl
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from excelapp import updater  # noqa: E402


def test_ssl_context_is_valid():
    ctx = updater._ssl_context()
    assert isinstance(ctx, ssl.SSLContext)
    # Phai bat xac thuc chung chi (khong tat verify)
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_ssl_context_cached():
    assert updater._ssl_context() is updater._ssl_context()


def test_version_compare_numeric():
    # 0.10.0 phai duoc coi la moi hon 0.9.0 (so sanh theo so, khong theo chuoi)
    assert updater.is_newer("0.10.0", "0.9.0") is True
    assert updater.is_newer("v0.10.1", "0.10.0") is True
    assert updater.is_newer("0.9.0", "0.10.0") is False
