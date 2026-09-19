import json, os, sys, urllib.request, urllib.error, winreg
k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
key, _ = winreg.QueryValueEx(k, "DEEPSEEK_API_KEY")
req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=json.dumps({"model": "deepseek-chat",
                     "messages": [{"role": "user", "content": "reply with the single word OK"}],
                     "max_tokens": 5}).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    method="POST")
try:
    body = json.loads(urllib.request.urlopen(req, timeout=40).read())
    print("DeepSeek: OK ->", body["choices"][0]["message"]["content"].strip()[:40])
except urllib.error.HTTPError as e:
    print("DeepSeek HTTP", e.code, e.read()[:160].decode("utf-8", "replace"))
except Exception as e:
    print("DeepSeek ERR", type(e).__name__, str(e)[:120])
print("key length:", len(key), "(not printed)")
