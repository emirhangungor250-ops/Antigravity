"""3 testi paralel çalıştır, biter bitmez lokale indir."""
import asyncio, json, os, sys, time
import urllib.request

sys.path.append(os.getcwd())
from test_e2e_pipeline import run

TESTS = [
    ("skincare", "https://www.trendyol.com/the-ordinary/niacinamide-10-zinc-1-30-ml-p-67669559"),
    ("tech",     "https://www.apple.com/tr/shop/buy-airpods/airpods-pro"),
    ("fashion",  "https://www.nike.com/tr/t/air-force-1-07-erkek-ayakkabisi-jbrhcr/CW2288-111"),
]

OUT_DIR = "test_videos"
os.makedirs(OUT_DIR, exist_ok=True)


async def run_and_download(category, url):
    out = await run(category, url)
    video_url = out["result"].get("video_url")
    if not video_url:
        print(f"❌ {category}: video URL yok")
        return out
    local = f"{OUT_DIR}/{category}.mp4"
    print(f"⬇️  {category}: indiriliyor → {local}", flush=True)
    try:
        urllib.request.urlretrieve(video_url, local)
        size_mb = os.path.getsize(local) / 1024 / 1024
        print(f"✅ {category}: {size_mb:.1f}MB kaydedildi → {os.path.abspath(local)}", flush=True)
        out["local_file"] = os.path.abspath(local)
    except Exception as e:
        print(f"❌ {category}: indirme başarısız — {e}", flush=True)
    return out


async def main():
    t0 = time.time()
    results = await asyncio.gather(*[run_and_download(c, u) for c, u in TESTS])
    print(f"\n{'='*70}\nTOPLAM SÜRE: {time.time()-t0:.1f}s\n{'='*70}")
    for r in results:
        print(f"  {r['category']:10s}  {r.get('local_file', 'YOK')}  ${r['scenario']['cost'].get('total_usd')}")


if __name__ == "__main__":
    asyncio.run(main())
