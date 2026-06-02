"""Chạy ứng dụng trực tiếp: python run.py [đường_dẫn_file]"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from excelapp.main import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
