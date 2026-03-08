# QuickUserlistExport

QuickUserlistExport is a local utility that exports the member list of a Discord server to a CSV file using a bot that you create and install in your own server.

This tool runs locally on your computer. It does not store data remotely and does not require any hosted service.

---

# 2-Minute Quick Setup

If you just want the shortest possible setup path, do this:

1. Go to the Discord Developer Portal:
   https://discord.com/developers/applications
2. Create a new application.
3. Open **Installation** and enable:
   - `Guild Install`
   - `Discord Provided Link`
   - `applications.commands`
   - `bot`
   - Bot Permission: `Administrator`
4. Open **Bot** and:
   - create the bot if needed
   - leave **Public Bot** on if Discord requires it to save
   - turn on **Server Members Intent**
5. Copy the install link from **Installation** and install the bot into your server.
6. Copy the **bot token** from the **Bot** page.
7. Turn on **Developer Mode** in Discord and copy your **Server ID**.
8. Open **QuickUserlistExport.exe**
9. Enter:
   - Bot Token
   - Server ID
   - Save Folder
10. Click **Validate**
11. Export either:
   - the full member list, or
   - a role-specific list

If anything fails, read the troubleshooting section below.

---

# What This Tool Does

QuickUserlistExport allows you to:

- Export all server members to a CSV file
- Export members belonging to a specific role
- Automatically paginate large servers
- Automatically name the export file using the server’s public name

Example export names:

- `MyServer_memberlist.csv`
- `MyServer_Moderatorlist.csv`

---

# Requirements

You must:

- Have permission to manage the Discord server
- Create a Discord bot
- Install that bot into the server
- Enable **Server Members Intent**

The tool then uses the bot token to query the Discord API.

---

# Overview of the Setup Process

You will perform these steps:

1. Create a Discord Application
2. Create a Bot inside that application
3. Enable the Server Members Intent
4. Generate an install link
5. Install the bot into your server
6. Copy the bot token
7. Copy the server ID
8. Enter both into QuickUserlistExport

The entire setup typically takes 3–5 minutes.

---

# Step 1 — Open the Discord Developer Portal

Go to:

https://discord.com/developers/applications

Click:

`New Application`

Give the application a name such as:

`Quick Userlist Export`

Click **Create**.

---

# Step 2 — Configure Installation Settings

Open the **Installation** page.

Set the following:

## Installation Contexts

Enable:

`Guild Install`

User install is not needed for this tool.

## Install Link

Set:

`Discord Provided Link`

## Default Install Settings (Guild Install)

Enable these scopes:

- `applications.commands`
- `bot`

When you enable **bot**, a permission selector appears.

Set permissions to:

`Administrator`

This is the easiest option for internal tools.

---

# Step 3 — Configure the Bot

Open the **Bot** tab.

If a bot does not exist yet, click:

`Add Bot`

Then configure:

## Public Bot

Leave this **ON** if Discord refuses to save the install settings when it is disabled.

This does not make the bot publicly listed.

## Privileged Gateway Intents

Enable:

`Server Members Intent`

This is required to export server member lists.

Save changes.

---

# Step 4 — Install the Bot Into Your Server

Return to the **Installation** page.

Copy the **Install Link**.

Open the link in your browser.

Select your server.

Click:

`Authorize`

The bot will now appear in your server’s member list.

---

# Step 5 — Get the Bot Token

Go back to the **Bot** page.

Find the section labeled:

`Token`

Click:

`Reset Token`

or

`Copy Token`

Copy the token.

Treat this token like a password.

Anyone with this token can control the bot.

---

# Step 6 — Get the Server ID

Enable **Developer Mode** in Discord if it is not already enabled.

In Discord:

`User Settings → Advanced → Developer Mode`

Then:

1. Right-click your server
2. Click **Copy Server ID**

Paste that ID into QuickUserlistExport.

---

# Step 7 — Run QuickUserlistExport

Launch:

`QuickUserlistExport.exe`

Enter:

- Bot Token
- Server ID
- Save Directory

Then click:

`Validate`

If validation succeeds you can:

- Load Roles
- Export Member List
- Export Role List

---

# Export Output

Exports are saved as CSV files.

Example:

- `MyServer_memberlist.csv`
- `MyServer_Moderatorlist.csv`

These files can be opened in:

- Excel
- Google Sheets
- LibreOffice
- Notepad

---

# Detailed Notes on the Discord Developer Portal

You may see several fields in the Developer Portal that are not needed for this tool.

## Client ID

The Client ID is the public identifier for your application.

It is not a password.

## Client Secret

The Client Secret is used for OAuth login and token exchange flows.

QuickUserlistExport does not use it.

## Redirect URI

Redirect URIs are used when Discord sends a user back to your application after an OAuth login.

QuickUserlistExport does not use browser login, so you do not need this.

## OAuth2 URL Generator

You do not need to use the OAuth2 URL Generator for this tool.

Use the **Installation** page and the **Discord Provided Link** instead.

---

# Recommended Developer Portal Settings Summary

Use these exact settings unless you have a specific reason not to:

## Installation Page

- Installation Contexts: `Guild Install`
- Install Link: `Discord Provided Link`

## Default Install Settings → Guild Install

- `applications.commands`
- `bot`

## Bot Permissions

- `Administrator`

## Bot Page

- Public Bot: `On` if needed to save/install with the default link
- Server Members Intent: `On`

---

# Troubleshooting

## Bot Does Not Appear to Be Installed

Check:

1. The bot was installed using the install link
2. You selected the correct server
3. The server ID entered into the program is correct
4. The token belongs to the same bot application

## Export Fails or Returns No Members

Check:

1. Server Members Intent is enabled
2. You clicked **Save Changes** after enabling it
3. The bot is installed in the server
4. The token has not been reset since installation

## Token Does Not Work

If the token fails validation:

1. Reset the token on the **Bot** page
2. Copy the new token
3. Paste it into the program again

## Validation Fails Even Though the Token Looks Correct

Check:

1. The bot is installed in the target server
2. The server ID is correct
3. The token belongs to the installed bot
4. Server Members Intent is enabled
5. You are not accidentally using the Client ID instead of the bot token

## I Am Confused by OAuth2 / Redirects

You can safely ignore these for this tool:

- Client Secret
- Redirect URI
- OAuth2 URL Generator

They are not part of the normal setup for QuickUserlistExport.

## Discord Won’t Let Me Save When Public Bot Is Off

If Discord gives an error like:

`Private application cannot have a default authorization link`

then leave **Public Bot** turned **on**.

That does not automatically make the bot publicly discoverable in any practical sense for this tool.

---

# Security Notes

QuickUserlistExport does not upload or transmit data anywhere except directly to Discord’s API.

However:

- Keep your bot token private
- Do not share it publicly
- Reset it if you believe it has been exposed

Anyone with the bot token can act as that bot.

---

# Building the Program Yourself

If you are compiling the Python source, build the EXE with:

`pyinstaller --noconfirm --clean --onefile --windowed --icon="youricon.ico" --name="QuickUserlistExport" --add-data="QUE Readme.md;." QuickUserlistExport.py`

This creates:

`QuickUserlistExport.exe`

The README will automatically be written next to the EXE on first run.

---

# File Naming and Save Behavior

The program allows you to choose a save folder.

By default, it should point to your Downloads folder when available.

Export names use the server’s public name:

- `ServerName_memberlist.csv`
- `ServerName_RoleNamelist.csv`

If a role is selected, the role export uses the role name in the filename.

---

# Notes

This tool is intended for administrators exporting member data from servers they control.

Always follow Discord’s terms of service and respect server privacy policies when exporting data.
