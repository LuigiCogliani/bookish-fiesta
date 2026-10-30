# Semantic Search PoC Deployment Guide

## Goal

Run a semantic search application in a Docker container on Laptop A and allow a user outside of the local wifi to access it

---

## Architecture



## Build Docker Image

### Where

PowerShell

Execute:

```powershell
docker build -t semantic-search-app .
```

Check:

```powershell
docker images
```

---

## Run Docker Container

### Where

PowerShell

Execute:

```powershell
docker run -p 7860:7860 semantic-search-app
```

Verify locally:

```text
http://localhost:7860
```

The application should behave exactly as it did before packaging.

---

## Install Cloudflare Tunnel

### Where

Same device that is running the container

Install:

```powershell
winget install --id Cloudflare.cloudflared
```

Verify:

```powershell
cloudflared version
```

---

## Create Public URL

### Where

New PowerShell window

Leave Docker running.

Execute:

```powershell
cloudflared tunnel --url http://localhost:7860
```

Cloudflare returns a temporary public URL:

```text
https://random-name.trycloudflare.com
```

---

## Test Public Access


### Remote Test

Send the URL:

```text
https://random-name.trycloudflare.com
```

to a remote user.

They should be able to:

1. Open the page.
2. Type a query.
3. Press Enter.
4. Receive the top 5 search results.

---

## Shut Down

### Stop Cloudflare Tunnel

In the Cloudflare terminal:

```text
Ctrl + C
```

### Stop Docker Container

Find container:

```powershell
docker ps
```

Stop container:

```powershell
docker stop <container-id>
```

The public URL will immediately stop working.

---

