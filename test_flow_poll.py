import httpx
import re
import urllib.parse
import json

cookies_str = "SEARCH_SAMESITE=CgQImKEB; APISID=iNO7dKWjF9AL9IFX/AEd8UG5y5_rzPWjiW; SAPISID=1BgtIeSn6kvarlj_/A6kOa1ObRUwrmiUeZ; __Secure-1PAPISID=1BgtIeSn6kvarlj_/A6kOa1ObRUwrmiUeZ; __Secure-3PAPISID=1BgtIeSn6kvarlj_/A6kOa1ObRUwrmiUeZ; OGPC=19024362-1:; OGP=-19024362:; SID=g.a000CgktBz1hkFxkCYdRNrCY3ls6LC1sohb9xz3z9IJSa8uBClWeNgFpRsWDLmBu3GZ1GQlS8wACgYKAUwSARUSFQHGX2MiD78wwY_MZ_YLC0bTeOZBMBoVAUF8yKrtWf_F2GRfEMvNEcMp6q6k0076; _ga=GA1.1.550855277.1790061987; _ga_X2GNH8R5NS=GS2.1.s1790061987$o1$g1$t1790063016$j60$l0$h730365438; SIDCC=AKEyXzU4HIcHVnKEi4WppwMAO4BINSzjI292GBZnKkvqLsb1TBZ0bVTYASpNcOJrSS9wIMHmnA"

cookies = {k: v for k, v in [i.split('=', 1) for i in cookies_str.split('; ') if '=' in i]}

# Let's test calling ngNC2 (Project Status/Media Poll) and ogiZ0b on labs.google/fx
host = "https://labs.google/fx"
path = "/_/AiSandboxAngularFrontend/data/batchexecute?rpcids=ngNC2&source-path=%2Fproject%2Faf8f43f9-b79b-45e6-a331-12efb66f0fb9&bl=boq_labs-ai-sandbox-frontend_20260920.04_p1&f.sid=4322680810250084447&hl=en-US&_reqid=20801585&rt=c"
url = host + path

body = "f.req=%5B%5B%5B%22ngNC2%22%2C%22%5B%5C%22tools%2FPINHOLE%2Fprojects%2Faf8f43f9-b79b-45e6-a331-12efb66f0fb9%5C%22%5D%22%2Cnull%2C%22generic%22%5D%5D%5D&at=AIQ-s5gZsdCOwYRS55FvOZidEJyW%3A1790062018173&"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    "X-Same-Domain": "1",
    "Origin": "https://labs.google",
    "Referer": "https://labs.google/fx/project/af8f43f9-b79b-45e6-a331-12efb66f0fb9/"
}

print("Testing ngNC2 project query...")
try:
    res = httpx.post(url, content=body, headers=headers, cookies=cookies, timeout=20.0)
    print("Status:", res.status_code)
    print("Response Length:", len(res.text))
    print("Preview:\n", res.text[:400])
    
    # Search for image/video URLs
    urls = re.findall(r'https?://[^\s"\'\\\]]+', res.text)
    media_urls = [u for u in urls if any(k in u.lower() for k in ['googleusercontent', 'image', 'video', 'lh3', 'mp4', 'png', 'jpg'])]
    print("\nMedia URLs found in project:")
    for m in set(media_urls):
        print(" ->", m)
except Exception as e:
    print("Error:", e)
