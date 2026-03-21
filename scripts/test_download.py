import requests

def test_url(url):
    try:
        res = requests.get(url, timeout=5)
        print(f"URL: {url}")
        print(f"Status: {res.status_code}")
        print(f"Type: {res.headers.get('Content-Type')}")
        print(f"Hex: {res.content[:4].hex()}")
        print("-" * 20)
    except Exception as e:
        print(f"Error {url}: {e}")

# Base Permutations
for user in ["hugoxxxx", "hugoxuuuu", "hugox"]:
    for repo in ["gt23_assets", "GT23_Assets", "GT23_Workflow"]:
        test_url(f"https://gitee.com/{user}/{repo}/repository/archive/main.zip")
