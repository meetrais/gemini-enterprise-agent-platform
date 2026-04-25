# 01 - Prerequisites

Before writing a line of agent code, get your local machine and your Google Cloud account set up.

## 1.1 Google Cloud account

1. Go to https://console.cloud.google.com and sign in.
2. If you're new, click **Activate** on the $300 free credit banner. New customers get **$300 in free credits** for Google Cloud products.
3. Create a billing account if you don't have one (Billing -> Manage billing accounts -> Create account). You need a billing account attached to the project even when using free credits.

## 1.2 Pick the Gemini Enterprise edition you'll target

This affects what features you can demo at the end. Pick now so you don't get surprised in section 13.

- **Standard** - core Gemini Enterprise app, enterprise security, connectors, and agent access.
- **Plus** - larger storage/indexing allowances and the broadest enterprise feature set.
- **Frontline** - for frontline workers; requires a Standard or Plus environment.

Most developer steps use Google Cloud services directly. Section 13 needs an existing Gemini Enterprise app and the right admin permissions.

## 1.3 Required IAM roles on the project

Ask your GCP admin to grant your user the following roles on the project you'll use, or grant them yourself if you have org admin:

- `roles/aiplatform.user` - Vertex AI user access
- `roles/run.sourceDeveloper` - Cloud Run Source Developer (for Cloud Run deploys)
- `roles/iam.serviceAccountUser` - Service Account User
- `roles/serviceusage.serviceUsageAdmin` - to enable APIs
- `roles/storage.admin` - for the staging Cloud Storage bucket
- `roles/discoveryengine.admin` - for Gemini Enterprise app agent registration in section 13
- `roles/resourcemanager.projectCreator` - only if you'll create projects yourself

## 1.4 Install local software

### 1.4.1 Python 3.10 or later

ADK requires Python 3.10 or later.

**Windows**

1. Download the latest Python 3.12 installer from https://www.python.org/downloads/windows/.
2. Run it. **Important:** check **"Add python.exe to PATH"** before clicking *Install Now*.
3. Verify in a new PowerShell window:

```powershell
PS> python --version
PS> pip --version
```

**macOS**

```bash
$ brew install python@3.12
$ python3 --version
$ python3 -m pip --version
```

**Linux**

Use your distro package manager or `pyenv`. On Debian/Ubuntu:

```bash
$ sudo apt-get update
$ sudo apt-get install -y python3 python3-venv python3-pip
$ python3 --version
$ python3 -m pip --version
```

### 1.4.2 Google Cloud CLI (`gcloud`)

Install from https://cloud.google.com/sdk/docs/install. The page has current installers for Windows, macOS, Debian/Ubuntu, Red Hat/Fedora/CentOS, and archive-based installs.

After installation, initialize and verify:

```powershell
PS> gcloud --version
PS> gcloud init
PS> gcloud auth list
```

```bash
$ gcloud --version
$ gcloud init
$ gcloud auth list
```

### 1.4.3 Git

```powershell
PS> git --version
```

```bash
$ git --version
```

Install from https://git-scm.com/downloads or your package manager.

### 1.4.4 Docker (optional, only for GKE / custom containers)

Install Docker Desktop on Windows/macOS or Docker Engine on Linux. Verify:

```powershell
PS> docker --version
```

```bash
$ docker --version
```

You can skip Docker if you'll only deploy to Vertex AI Agent Engine or Cloud Run source-based deploys.

### 1.4.5 Visual Studio Code (recommended editor)

1. Download from https://code.visualstudio.com/.
2. Install the **Python**, **Pylance**, and **Google Cloud Code** extensions.

## 1.5 Sign in to gcloud and set Application Default Credentials

In a fresh terminal:

```powershell
PS> gcloud auth login
PS> gcloud auth application-default login
```

```bash
$ gcloud auth login
$ gcloud auth application-default login
```

Both commands open your browser. The first logs the `gcloud` CLI in. The second creates local Application Default Credentials that the Python SDKs use automatically.

## 1.6 PowerShell execution policy (Windows only)

When you create Python virtual environments, the activation script is `.ps1`. By default, PowerShell may block running it. Allow it for your user:

```powershell
PS> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type **Y** to confirm. This affects only your account, not the whole machine.

## 1.7 Pick a working directory

Create one folder under your home directory for everything in this guide:

```powershell
PS> mkdir $HOME\agent-platform-demo
PS> cd $HOME\agent-platform-demo
```

```bash
$ mkdir -p "$HOME/agent-platform-demo"
$ cd "$HOME/agent-platform-demo"
```

You'll come back to this directory at the start of every section.

---

## What you should have now

- [ ] A Google Cloud account with billing and free credits applied.
- [ ] IAM roles granted on your project.
- [ ] Python 3.10+ installed and on PATH (`python --version` works).
- [ ] gcloud CLI installed and authenticated (`gcloud auth list` shows your account).
- [ ] Application Default Credentials configured.
- [ ] Git installed.
- [ ] Optional: Docker Desktop, VS Code.
- [ ] Windows only: PowerShell execution policy set to RemoteSigned for CurrentUser.
- [ ] A working directory at `~/agent-platform-demo`.

When all boxes are checked, move on to **`02_project_setup.md`**.
