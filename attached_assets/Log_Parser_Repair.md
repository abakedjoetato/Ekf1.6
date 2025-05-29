## 📄 EMERALD’S KILLFEED — LOG PARSER & CONNECTION SYSTEM REPAIR

🧩 **TASK TYPE:** SINGLE-TASK, MULTI-PHASE (No Output or Checkpoints Midway)

All subtasks below form **one complete task** and must be executed as a single atomic operation.
🚫 Do **not checkpoint, commit, or output** until every step is completed and verified.

---

### 📦 [PHASE 0] — PROJECT SETUP (ZIP INSTALLATION)

1. **Unpack Project Archive**
   - Locate the `.zip` file in `attached_assets`
   - Unzip all contents into the root of the workspace
   - If contents unpack into a subfolder, move all files and folders to the root directory

2. **Clean Workspace**
   - Remove all legacy folders, duplicate directories, empty folders, or broken symbolic links

3. **Setup Environment**
   - Confirm presence of `.env` or `config` file
   - Ensure Replit secrets include:
     - `BOT_TOKEN`
     - `MONGO_URI`

4. **Start the Bot**
   - Use the Replit “Run” button
   - Confirm:
     - Bot boots without errors
     - All cogs/modules are loaded
     - Slash commands sync successfully

---

### 🧠 [PHASE 1] — LOG PARSER & CONNECTION SYSTEM DIAGNOSIS

#### 🔍 Audit Goals:

- Load and analyze the included `Deadside.log` file from `attached_assets`
- Examine parsing logic and regex patterns to detect:
  - Queue entries (login requests)
  - Player joins (registration lines)
  - Disconnects (both before and after join)
  - Airdrops (status: `Flying`)
  - Heli crashes (status: `Initial`)
  - Trader appearances (status: `Initial`)
  - Missions (state: `Ready`, Level ≥ 3)
  - ❌ Suppress output for: Construction saves, Encounter resets

#### 🧠 Player Lifecycle Flags:

- `jq` = Queued
- `j2` = Joined
- `d1` = Disconnected after join
- `d2` = Disconnected before join

#### ⚖️ Count Logic:
- `Player Count (PC) = j2 - d1`
- `Queue Count (QC) = jq - j2 - d2`

These values must be tracked per server and used for:
- Voice channel updates
- Connection feed updates

---

### 🛠 [PHASE 2] — IMPLEMENTATION & COMMANDS

- [ ] Add `/resetlogparser` command:
  - Clears last parsed line
  - Resets player count

- [ ] Inject cold start context to log parser
  - Provide player state on bot init

- [ ] Validate parser continuation:
  - Must continue from last line
  - Must reset correctly when a new `Deadside.log` is detected

- [ ] Clean legacy/test commands and redundant code

---

### 📊 [PHASE 3] — VALIDATION USING INCLUDED LOG FILE

- [ ] Parse included `Deadside.log`
- [ ] Output or log the following:
  - Count of: Joins, disconnects, queues
  - Count of each mission type, trader, heli crash, and airdrop
  - Final calculated PC and QC (must not be zero)
- [ ] Output must use `EmbedFactory`
- [ ] Channel routing must match configuration

---

## ✅ COMPLETION CRITERIA

- [ ] Bot is running and stable
- [ ] All parsing patterns match the included log
- [ ] Full lifecycle tracking works
- [ ] Event outputs match specification and embed format
- [ ] Parser continues correctly and resets on new file
- [ ] No unnecessary commands remain

---

## 🔐 DEVELOPMENT STANDARDS

- ✅ Use only `pycord 2.6.1` — **do not use `discord.py`**
- ✅ Do not guess — validate every regex with the provided log
- ✅ Ensure multi-guild, multi-server isolation
- ❌ No commits, checkpoints, or partial outputs
- ✅ EmbedFactory must be used for all outputs
- ✅ All code must be final, clean, and verified