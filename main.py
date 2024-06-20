from fastapi import FastAPI, Request, HTTPException, Response
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
import os
from datetime import datetime
import uvicorn
import json

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
        send_email(payload)
        return Response(content=json.dumps({"message": "Webhook received successfully"}), status_code=200, media_type="application/json")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/")
async def test(request: Request):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
         
        return Response(content=json.dumps({"fechahora": current_time, "deploy": config("DEPLOY")}), status_code=200, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def send_email(payload):
    payload = json.dumps(payload, indent=4)
    subject = 'GITHUB CAMBIOS'
    body = f'PAYLOAD: {payload}'

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
