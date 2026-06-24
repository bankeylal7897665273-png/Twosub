from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import subprocess
import uuid
import pexpect

app = FastAPI()

# CORS issue fix karne ke liye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API 100% active. Naya deploy aur update dono kaam karenge!"}

# ==========================================
# 1. TOKEN GENERATE KARNE WALI API
# ==========================================
@app.post("/get-token")
def get_token(email: str = Form(...), password: str = Form(...)):
    try:
        child = pexpect.spawn('surge login', encoding='utf-8', timeout=15)
        child.expect(['email:', 'Login:'], timeout=5)
        child.sendline(email)
        child.expect('password:', timeout=5)
        child.sendline(password)
        child.expect(pexpect.EOF)
        
        child2 = pexpect.spawn('surge token', encoding='utf-8', timeout=15)
        child2.expect(pexpect.EOF)
        output = child2.before.strip()
        
        lines = output.split('\n')
        token = lines[-1].strip()
        
        return {
            "status": "success", 
            "email": email, 
            "token": token, 
            "message": "Yeh raha token! Ab isko Hugging Face Settings (Secrets) mein SURGE_LOGIN aur SURGE_TOKEN ke naam se save kar lo."
        }
    except Exception as e:
        return {"status": "error", "message": "Token generate nahi ho paya.", "error_log": str(e)}

# ==========================================
# 2. DEPLOY & UPDATE WALI API
# ==========================================
@app.post("/deploy")
async def deploy_code(subdomain: str = Form(...), zip_file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    extract_dir = f"/tmp/{task_id}"
    zip_path = f"{extract_dir}.zip"

    try:
        # Zip save karna
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(zip_file.file, buffer)
            
        # YAHAN FIX KIYA HAI: Agar zip extract nahi hui toh crash hone se bachayega
        try:
            shutil.unpack_archive(zip_path, extract_dir)
        except Exception as unpack_err:
            return {"status": "error", "message": "File unzip nahi ho payi. Dhyan rahe sirf .zip file hi upload karni hai, direct HTML file nahi!"}

        if not subdomain.endswith(".surge.sh"):
            full_domain = f"{subdomain}.surge.sh"
        else:
            full_domain = subdomain

        # Deploy command
        process = subprocess.run(
            ["surge", extract_dir, full_domain],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            "status": "success", 
            "url": f"https://{full_domain}", 
            "message": "Files successfully live/update ho gayi!"
        }
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error", 
            "message": "Deploy/Update mein problem aayi",
            "error_log": e.stderr
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Server par unknown error aaya",
            "error_log": str(e)
        }
        
    finally:
        # Temp files delete karna
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
