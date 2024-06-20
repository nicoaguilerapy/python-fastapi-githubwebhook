from fastapi import FastAPI, Request, HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from decouple import config
import os
from datetime import datetime
import uvicorn

app = FastAPI()

# Configuración del servidor de correo
SMTP_SERVER = config("SMTP_SERVER")
SMTP_PORT = int(config("SMTP_PORT"))
SMTP_USERNAME = config("SMTP_USERNAME")
SMTP_PASSWORD = config("SMTP_PASSWORD")
EMAIL_FROM = config("SMTP_USERNAME")
EMAIL_TO = config("EMAIL_TO")

@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        payload = await request.json()
        
        if 'ref' in payload and payload['ref'] == 'refs/heads/master_main':
            commit_message = payload['head_commit']['message']
            commit_url = payload['head_commit']['url']
            send_email(commit_message, commit_url)
        
        return {"commit_message": commit_message, "commit_url":commit_url}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/test")
async def test(request: Request):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {"fechahora": current_time, "deploy":config("DEPLOY")}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def send_email(commit_message, commit_url):
    subject = 'New commit in master_main branch'
    body = f'There was a new commit in the master_main branch.\n\nCommit message: {commit_message}\nCommit URL: {commit_url}'

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = ", ".join(EMAIL_TO)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_FROM, EMAIL_TO, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    if config("DEPLOY") == "N":
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        if "DYNO" in os.environ:
            workers = int(os.environ.get("WEB_CONCURRENCY", 1))
            timeout = int(os.environ.get("WEB_TIMEOUT", 120))
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), workers=workers, timeout_keep_alive=timeout)
        else:
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
