# -*- coding: utf-8 -*-
"""Cron giriş noktası — periyodik (ör. birkaç saatte bir, gündüz) çalışacak şekilde
zamanla. Tek tur çalışır ve çıkar (cron'a uygun)."""
import sys
from core import pipeline


def main():
    lines = pipeline.run()
    for ln in lines:
        print(ln, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
