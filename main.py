from fastapi import FastAPI, Request, HTTPException, Response
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
import os
from datetime import datetime
import uvicorn
import json
import threading

app = FastAPI()

# Configuración del servidor de correo
SMTP_SERVER = config("SMTP_SERVER")
SMTP_PORT = int(config("SMTP_PORT"))
SMTP_USERNAME = config("SMTP_USERNAME")
SMTP_PASSWORD = config("SMTP_PASSWORD")
EMAIL_FROM = config("SMTP_USERNAME")
EMAIL_TO = [email.strip() for email in config("EMAIL_TO").split(",")]
BRANCH = config("BRANCH")


@app.post("/webhook")
async def github_webhook(request: Request):
    try:
        payload = await request.json()
        threading.Thread(target=send_email, args=(payload,)).start()
        
        return Response(content=json.dumps({"message": "OPERACIÓN EXITOSA"}), status_code=200, media_type="application/json")

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
    if payload['ref'] != 'refs/heads/'+BRANCH:
        return
    subject = 'NUEVO COMMIT EN '+BRANCH
    commit_author = payload['head_commit']['author']['name']
    commit_message = payload['head_commit']['message']
    commit_url = payload['head_commit']['url']
    commit_date = payload['head_commit']['timestamp']

    # Listar archivos modificados, eliminados y agregados
    added_files = payload['head_commit'].get('added', [])
    removed_files = payload['head_commit'].get('removed', [])
    modified_files = payload['head_commit'].get('modified', [])

    body = f"""
        Commit by: {commit_author}
        Commit message: {commit_message}
        Commit URL: {commit_url}
        Commit date: {commit_date}

        Agregados ({len(added_files)}):
        {chr(10).join(added_files)}

        Eliminados ({len(removed_files)}):
        {chr(10).join(removed_files)}

        Modificados ({len(modified_files)}):
        {chr(10).join(modified_files)}
        """

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
            uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get(
                "PORT", 8000)), workers=workers, timeout_keep_alive=timeout)
        else:
            uvicorn.run(app, host="0.0.0.0", port=int(
                os.environ.get("PORT", 8000)))
