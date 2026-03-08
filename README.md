QuickUserlistExport is a local utility that exports the member list of a Discord server to an Excel `.xlsx` file using a bot that you create and install in your own server.

This tool runs locally on your computer. It does not use a hosted service, and it does not require slash commands or bot interaction inside Discord after setup.

---

Quick Setup

1. Go to the Discord Developer Portal:  
   `https://discord.com/developers/applications`
2. Create a new application.
3. Open **Installation** and set:
   - **Guild Install** enabled
   - **Discord Provided Link**
   - scopes: `applications.commands` and `bot`
   - bot permission: `Administrator`
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
10. Click **Validate Bot Access**
11. Export either:
   - the full member list, or
   - a role-specific list

If anything fails, read the troubleshooting section below.

---

# What This Tool Does

QuickUserlistExport allows you to:

- Export **all non-bot server members** to an Excel workbook
- Export members belonging to a **specific role**
- Works for servers over 1000 (there is theoretically no limit)
- DARK MODE IS DEFAULT!!! as is only proper, moral, correct, and good.
- Save preferences such as the server ID, save folder, dark mode, and optionally the bot token

# Exported Columns

The spreadsheet exports these columns:

- `user_id`
- `username`
- `display_name`
- `joined_at`
- `highest_role`

Additional export behavior:

- **Bot accounts are skipped**
- If a user has a non-zero discriminator, the username is exported as `username#1234`---

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
3. Enable the **Server Members Intent**
4. Generate an install link
5. Install the bot into your server
6. Copy the bot token
7. Copy the server ID
8. Enter both into QuickUserlistExport

The entire setup typically takes **3–5 minutes**.

---

# Step 1 — Open the Discord Developer Portal

Go to:

`https://discord.com/developers/applications`

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

This is the simplest option for a private admin tool.

---

# Step 3 — Configure the Bot

Open the **Bot** tab.

If a bot does not exist yet, click:

`Add Bot`

Then configure:

## Public Bot

Leave this **ON** if Discord refuses to save the install settings when it is disabled.

This does not automatically publish the bot in a public bot listing for practical purposes here.

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

The bot should now appear in your server’s member list.

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

- **Bot Token**
Paste the bot token from the Discord Developer Portal.
- **Server ID**
Paste the numeric server ID copied from Discord with Developer Mode enabled.
- **Save Folder**
Choose where exported Excel files should go. The default is your **Downloads** folder when available.

Then click:

`Validate Bot Access`
Checks that:

- the token is valid
- the bot can access the target server
- the server ID is valid
- roles can be retrieved

If validation succeeds you can:

- **Load Roles**
Loads the list of roles from the validated server so you can export only one role if desired.
- **Generate Memberlist**
Exports all non-bot members to an `.xlsx` file.
- **Generate Role List**
Exports only members who have the selected role.


### Save Settings
Saves current app preferences locally.

### Open README
Opens this README file from the same folder as the program.

---

# Troubleshooting

## The bot could not access the server

This usually means one of these is true:

- the bot is not installed in that server
- the server ID is wrong
- the token belongs to a different bot
- the token is invalid

Check:

1. The bot was installed using the install link
2. You selected the correct server during installation
3. The server ID entered into the program is correct
4. The token belongs to the same bot application

---

## Validation works, but export fails

Check:

1. **Server Members Intent** is enabled
2. You clicked **Save Changes** after enabling it
3. The bot is installed in the server
4. The token has not been reset since installation

---

## Roles do not load

Possible causes:

- wrong Server ID
- wrong bot token
- bot not installed in that server
- Discord API/network problem

---

## Token looks right, but it still fails

Check:

1. You copied the **bot token**, not the Client ID
2. The token was not reset after you copied it
3. The token belongs to the bot installed in the server

---

## I am confused by OAuth2 / Redirects

You may see these fields in the Developer Portal:

- Client ID
- Client Secret
- Redirect URI
- OAuth2 URL Generator

These are **not needed** for normal use of QuickUserlistExport.

Use the **Installation** page and the **Discord Provided Link** instead.

---

## Export file opens with strange formatting

The current version exports directly to `.xlsx`, so names with tabs/newlines should no longer break columns the way text-delimited exports can.

If a spreadsheet still looks wrong:

1. confirm the file actually ends in `.xlsx`
2. confirm your spreadsheet program fully supports Excel workbooks
3. try opening the same file in Excel or LibreOffice Calc

---

## Dark mode looks wrong after editing the code

Check that:

1. `self.apply_theme()` is called during startup
2. the donation label is a `tk.Label`
3. the donation label is styled directly inside `apply_theme()`
4. there are no leftover references to a removed `self.footer`

---

# Security Notes

QuickUserlistExport does not upload or transmit data anywhere except directly to Discord’s API.

However:

- Keep your bot token private
- Do not share it publicly
- Reset it if you believe it has been exposed

Anyone with the bot token can act as that bot.

---

# Packaging Into an EXE

If you are compiling the Python source, build the EXE with:

```bash
pyinstaller --noconfirm --clean --onefile --windowed --icon="QUEicon.ico" --name="QuickUserlistExport" --add-data="QUE Readme.md;." QuickUserlistExport.py
