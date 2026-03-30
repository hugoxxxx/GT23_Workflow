import os
import requests
import zipfile
import io

def diag_zip():
    GITEE_TOKEN = "e6310b92bf4609c5f55e09f78fe4415a"
    zip_url = f"https://gitee.com/api/v5/repos/hugoxuuuu/gt23_assets/zipball?access_token={GITEE_TOKEN}"
    
    headers = {
        'User-Agent': 'GT23-Workflow-Client',
        'Referer': 'https://gitee.com/hugoxuuuu/gt23_assets'
    }
    
    print(f"Downloading ZIP from: {zip_url}")
    res = requests.get(zip_url, timeout=30, headers=headers)
    if res.status_code == 200:
        print("Download successful.")
        with zipfile.ZipFile(io.BytesIO(res.content)) as z:
            namelist = z.namelist()
            print(f"Total entries: {len(namelist)}")
            print("First 20 entries:")
            for name in namelist[:20]:
                print(f"  {name}")
            
            root_in_zip = namelist[0].split('/')[0]
            print(f"Detected root_in_zip: {root_in_zip}")
    else:
        print(f"Download failed: {res.status_code}")

if __name__ == "__main__":
    diag_zip()
