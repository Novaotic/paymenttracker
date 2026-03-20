# Run as a Linux Service (systemd)

This guide runs Payment Tracker as a persistent `systemd` service that starts on boot.

---

## 1) Prepare app directory and dependencies

On the Linux machine:

```bash
cd /opt/paymenttracker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If your project is in another path, use that path consistently in the service file below.

---

## 2) Create a dedicated service user (recommended)

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin paymenttracker
sudo chown -R paymenttracker:paymenttracker /opt/paymenttracker
```

If this user already exists, skip these commands.

---

## 3) Create the systemd unit

Create `/etc/systemd/system/paymenttracker.service`:

```ini
[Unit]
Description=Payment Tracker FastAPI Service
After=network.target

[Service]
Type=simple
User=paymenttracker
Group=paymenttracker
WorkingDirectory=/opt/paymenttracker
ExecStart=/opt/paymenttracker/.venv/bin/python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Notes:
- Use `src.app:app` to match this project structure.
- Do **not** use `--reload` in production service mode.

---

## 4) Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable paymenttracker
sudo systemctl start paymenttracker
```

Check status:

```bash
sudo systemctl status paymenttracker
```

Follow logs:

```bash
sudo journalctl -u paymenttracker -f
```

---

## 5) Access from other devices

From another device on the same network, open:

- `http://<hostname>:8000` (preferred if hostname resolves), or
- `http://<server-ip>:8000`

If needed, open the port in your firewall (example for UFW):

```bash
sudo ufw allow 8000/tcp
```

---

## 6) Deploy updates

After pulling code changes or updating dependencies:

```bash
cd /opt/paymenttracker
source .venv/bin/activate
python -m pip install -r requirements.txt
sudo systemctl restart paymenttracker
```

---

## Troubleshooting

- Service not starting:
  - `sudo systemctl status paymenttracker`
  - `sudo journalctl -u paymenttracker -n 200 --no-pager`
- Import/module errors:
  - Confirm `WorkingDirectory` is the repo root.
  - Confirm `ExecStart` points to the virtualenv Python.
- Connection refused:
  - Confirm service is running.
  - Confirm port `8000` is open on firewall.
  - Confirm you are using `http://...`.
