# Operate the dashboard

## Connect and refresh

1. Enter the terminal address in **Starlink IP:**.
2. Click **Connect**. The client indicator shows whether the app connected to
   the device API. The Connection card shows the terminal's operational state;
   these are different statuses.
3. Read service status, self-test results, obstructions, terminal identity,
   firmware, UTC offset, and current and target alignment.
4. Read **Detailed Status & Alerts** for additional diagnostics.
5. Click **Refresh Now** for an immediate read. Automatic reads occur every five
   seconds while connected.
6. Click **Disconnect** to stop reads. Click **Exit** and confirm to close.

Choose Light, Dark, TRON, or Hackers in the **Theme:** selector. Theme changes
do not change the terminal configuration.

## Troubleshooting

If connection fails, check the terminal address, power, network path, and gRPC
service on port `9200`. Generate the protocol modules as described in
[setup](setup.md). To show diagnostic logs:

```console
python starlink_dashboard.py --debug
```

Review logs before sharing them. Terminal identifiers, location data, and
network addresses can identify your site.

## GPS privacy

The app rounds GPS coordinates to three decimal places by default, which
identifies a site to approximately 100 meters. This is reduced precision, not
anonymization. An exact coordinate shows the terminal's physical position.

To opt in to exact coordinates, set `STARLINK_DASHBOARD_EXACT_GPS` to `1`,
`true`, `yes`, or `on` before launch. For example, in PowerShell:

```powershell
$env:STARLINK_DASHBOARD_EXACT_GPS = "1"
python starlink_dashboard.py
```

On Linux or macOS:

```console
STARLINK_DASHBOARD_EXACT_GPS=1 python starlink_dashboard.py
```

Do not share screenshots or logs from a live terminal without reviewing and
removing sensitive data. Use the [synthetic screenshot capture](development.md)
for documentation images.
