# Quick Userlist Export README

## What this tool does

Quick Userlist Export connects to Discord with **your own bot token**, validates access to a server, and exports either:

- the full server member list, or
- only members with a selected role

It saves the export as a CSV file you can open in Excel, Google Sheets, LibreOffice Calc, or similar software.

## What you need before using it

1. A Discord application with a bot created in the Discord Developer Portal.
2. The bot token for that bot.
3. The bot installed in the target server.
4. The target server's numeric Server ID.
5. **Server Members Intent** enabled for the bot if you want the full member list export to work.

## First-time setup

### 1) Create a bot

Open the Discord Developer Portal and create a new application. Then add a bot user to that application.

### 2) Enable Server Members Intent

In the Developer Portal, open your bot settings and enable **Server Members Intent**.

Without this, the member export may validate successfully but fail when trying to download the full list.

### 3) Install the bot in your server

Use the application's install or OAuth2 page to invite the bot into your server.

The bot must be installed in the server you want to export.

### 4) Get the Server ID

Turn on Discord **Developer Mode**, then right-click the server icon and choose **Copy ID**.

### 5) Run the tool

Fill in:

- **Bot token**
- **Server ID**
- **Save folder**

Then click **Validate Bot Access**.

## What the buttons do

- **Validate Bot Access**: Confirms the token works and the bot can access the server.
- **Load Roles**: Loads the server's roles for the role-specific export.
- **Generate Memberlist**: Exports all members.
- **Generate Role List**: Exports only members who have the selected role.
- **Open README**: Opens this file.

## Default save behavior

The save folder defaults to your **Downloads** folder when available.

The default filenames are:

- `ServerName_memberlist.csv`
- `ServerName_RoleNamelist.csv`

The README is written next to the EXE the first time the program runs.

## Troubleshooting

### Error: The bot could not access that server

This usually means one of these is true:

- the bot is not installed in that server
- the Server ID is wrong
- the token belongs to a different bot
- the bot token is invalid or expired

Fixes:

1. Confirm the **Server ID** by copying it again with Developer Mode enabled.
2. Confirm the **bot token** by copying it again from the Developer Portal.
3. Confirm that the bot shown in the Developer Portal is the same one installed in the server.
4. Reinstall the bot using the install/invite flow.

### Error: Validation works, but exporting members fails

Most often, this means **Server Members Intent** is not enabled.

Fixes:

1. Open the Developer Portal.
2. Open your application.
3. Open the **Bot** page.
4. Enable **Server Members Intent**.
5. Save changes.
6. Run the export again.

### Error: Roles do not load

Possible causes:

- wrong Server ID
- wrong bot token
- bot not installed in that server
- Discord API/network problem

### Save folder error

If the button stays disabled or saving fails:

- confirm the save folder exists
- choose a writable folder such as Downloads or Desktop

## Security note

This tool is intended for server admins using **their own bot** and **their own token**.

Do not distribute a shared bot token inside a public EXE.

## Packaging into an EXE

Use this command in the same folder as:

- `QuickUserlistExport.py`
- `QUE Readme.md`
- `QUEicon.ico`

```bash
pyinstaller --noconfirm --clean --onefile --windowed --icon="QUEicon.ico" --name="QuickUserlistExport" --add-data="QUE Readme.md;." QuickUserlistExport.py
```

When the EXE runs for the first time, it writes `QUE Readme.md` next to the EXE automatically.
