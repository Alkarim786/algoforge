# Deploying AlgoForge

Production runs the whole stack with Docker Compose on one Linux server. [Caddy](https://caddyserver.com) serves the built frontend, proxies `/api` to FastAPI, and gets and renews the HTTPS certificate on its own.

```
Internet ──443──▶ web (Caddy: static site + HTTPS) ──/api──▶ api (FastAPI ×2) ──▶ db (PostgreSQL)
                                                                 │
                                                                 └──▶ redis (queue) ──▶ worker ×2 ──▶ sandbox container per test case
```

Only ports 80 and 443 are exposed. Postgres, Redis and the API are reachable only inside the Docker network.

## Why a server rather than Vercel, Render or Heroku

The judge starts a fresh Docker container for every test case. That needs a real Docker daemon. Platform-as-a-service hosts don't give you one, so the worker can't run there. Any Linux VPS can:

| Need | Recommended |
|---|---|
| OS | Ubuntu 24.04 LTS (any Linux with Docker works, x86-64 or ARM) |
| Size | 2 vCPU, 4 GB RAM, 40 GB disk handles a class-sized group; each extra judge worker needs about 0.5 vCPU |
| Providers | Hetzner, DigitalOcean, Linode, AWS Lightsail or EC2, Google Compute Engine, Oracle Cloud |
| Domain | Any registrar; you only need to add a DNS record |

Hosting for free? Follow [Free hosting on Oracle Cloud](#free-hosting-on-oracle-cloud) first, then come back for steps 3 to 8. Just want a public link from your own computer for now? See [Host from your own computer](#host-from-your-own-computer).

## First deployment

**1. Point your domain at the server.** In your DNS settings, add an `A` record for the domain (for example `algoforge.example.com`) with the server's IPv4 address, plus an `AAAA` record if it has IPv6. Wait until `ping algoforge.example.com` shows the server's address. HTTPS can't be issued before then.

**2. Open the firewall** (on the server, as a sudo user):

```bash
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw allow 443/udp && sudo ufw enable
```

Note: Docker publishes ports past ufw, but this stack publishes only 80 and 443, so nothing else is exposed. Some providers also have a separate cloud firewall; open 80 and 443 there too. On Oracle Cloud, skip this step and use the Oracle firewall steps instead; ufw clashes with Oracle's own rules.

**3. Install Docker:**

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # then log out and back in
```

**4. Get the code onto the server.** From a Git repository:

```bash
sudo mkdir -p /opt/algoforge && sudo chown $USER /opt/algoforge
git clone <your-repository-url> /opt/algoforge
cd /opt/algoforge
```

Or copy the project folder up with `scp -r` or `rsync`. Don't copy your development `.env`, `node_modules` or `frontend/public/monaco`.

**5. Create the production settings.** This generates fresh secrets and sets your domain:

```bash
python3 scripts/init_env.py --domain algoforge.example.com
```

`.env` now holds the database password, the JWT signing key and the admin API key. It is readable only by you. Never commit it.

**6. Deploy:**

```bash
./scripts/deploy.sh
```

This builds the images, runs the database migrations, starts everything, and loads the topics, problems, test cases and solution guides. The first build takes a few minutes. When it finishes, the site is live at `https://algoforge.example.com`.

**7. Create your admin account:**

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.create_admin <username> <email>
```

Then sign in at `https://algoforge.example.com/admin/login`.

**8. Turn on nightly backups:**

```bash
crontab -e
# add this line:
15 3 * * * /opt/algoforge/scripts/backup.sh >> /opt/algoforge/backups/backup.log 2>&1
```

Dumps go to `backups/` and are kept for 14 days. They're on the same disk as the database, so also copy them off the server regularly, for example with `rclone` to cloud storage, or by turning on your provider's volume snapshots. `scripts/backup.sh` explains how to restore one.

## Host from your own computer

No server needed: your computer runs the production stack, and a free Cloudflare quick tunnel gives it a public HTTPS address. You don't need a domain, an account, or router port-forwarding, and your home IP stays hidden. The site is online only while the computer is on, awake and running Docker, and the address changes each time the tunnel restarts. That makes it good for demos and sharing, not for permanent hosting.

**1. Create `.env`.** Run this once:

```bash
python scripts/init_env.py
```

Then add these lines to `.env`. `DOMAIN=:80` makes Caddy answer for the tunnel's address over plain HTTP; Cloudflare provides the HTTPS. The `127.0.0.1` ports keep the site off your local network.

```
DOMAIN=:80
HTTP_PORT=127.0.0.1:8080
HTTPS_PORT=127.0.0.1:8443
```

**2. Start the stack and the tunnel** (in the project folder):

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.tunnel.yml up -d --build --scale worker=2
docker compose -f docker-compose.prod.yml exec api python -m app.seed
```

**3. Find your public address.** It's the `https://….trycloudflare.com` line in:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.tunnel.yml logs tunnel
```

**4. Create your admin account:**

```bash
docker compose -f docker-compose.prod.yml exec api python -m app.create_admin <username> <email>
```

While it's running, `http://localhost:8080` also opens the site on this computer.

- **Stop:** `docker compose -f docker-compose.prod.yml -f docker-compose.tunnel.yml down` (your data is kept).
- **Stop only the public link:** `docker compose -f docker-compose.prod.yml -f docker-compose.tunnel.yml stop tunnel`.
- **Keep it reachable:** set Windows to never sleep while plugged in, and keep Docker Desktop running.
- **Safety:** user code runs in sandbox containers inside Docker Desktop's Linux VM, not directly on Windows. The judge worker controls Docker, though, so only keep the tunnel up while you need the site public, and keep Windows and Docker Desktop updated.

**A permanent address on this computer:** a free Cloudflare account plus a domain on Cloudflare gives you a *named* tunnel with a fixed address. Or move to a server (below) when you want the site always online.

## Free hosting on Oracle Cloud

Oracle's Always Free tier includes an ARM server with 2 CPUs and 12 GB of RAM that never expires. That's plenty for AlgoForge, and every image it uses runs on ARM. Together with a free DuckDNS subdomain, the site costs nothing.

**1. Create the account.** Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/). A card is needed to verify you, but Always Free resources are never charged.

- Pick your **home region** carefully: it can't be changed later, and free servers can only be created there. Choose one close to your users, such as India West (Mumbai) or India South (Hyderabad).
- Optional: upgrading the account to **Pay As You Go** keeps everything inside the free limits free. It also stops Oracle from reclaiming the server if it sits idle. Free-only accounts can lose servers that stay nearly idle for about a week.

**2. Create the server.** In the console, go to *Compute → Instances → Create instance*:

| Setting | Value |
|---|---|
| Image | Canonical Ubuntu 24.04 |
| Shape | *Change shape → Ampere →* `VM.Standard.A1.Flex`, **2 OCPUs, 12 GB memory** (look for the "Always Free-eligible" label) |
| Networking | Create a new virtual cloud network with a **public subnet**, and keep **Assign a public IPv4 address** on |
| SSH keys | *Generate a key pair for me* and download the private key, or paste your own public key |
| Boot volume | 50 GB is fine (up to 200 GB in total is free) |

If you get **"Out of host capacity"**, try a different availability domain in the same form, or try again later. Free ARM capacity in busy regions comes and goes.

When the instance is *Running*, copy its **public IP address** from the instance page.

**3. Open ports 80 and 443 in Oracle's cloud firewall.** On the instance page, open the subnet, then its *Default Security List*, then *Add Ingress Rules*. Add three rules, each with source `0.0.0.0/0`:

- TCP, destination port `80`
- TCP, destination port `443`
- UDP, destination port `443` (for HTTP/3)

**4. Open the same ports on the server itself.** Oracle's Ubuntu image has its own firewall rules that reject everything except SSH, so both firewalls need opening. This is the step most guides forget. Connect to the server:

```bash
ssh -i path/to/private-key ubuntu@<public-ip>
```

Then run:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p udp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

Don't enable ufw on this image; it conflicts with these rules.

**5. Get a free domain from DuckDNS.** Sign in at [duckdns.org](https://www.duckdns.org) and create a subdomain, for example `algoforge`. Set its IP to the server's public IP. Your site will be `algoforge.duckdns.org`. Check it resolves before deploying, so HTTPS can be issued:

```bash
ping algoforge.duckdns.org
```

The public IP stays the same as long as you don't terminate the instance. You can also turn it into a *reserved* IP in the console so it survives rebuilds.

**6. Continue with [First deployment](#first-deployment), steps 3 to 8.** Install Docker, get the code, then run:

```bash
python3 scripts/init_env.py --domain algoforge.duckdns.org
```

```bash
./scripts/deploy.sh
```

Then create your admin account and set up backups. The first build on ARM takes around 10 minutes; later deploys are faster.

The server has 2 CPUs, so keep `WORKERS=2` (the default). gVisor supports ARM too, so the gVisor steps under [Security](#security) work here as well.

## Updating

```bash
cd /opt/algoforge
git pull
./scripts/deploy.sh
```

Migrations run automatically. Users stay signed in, and submissions waiting in the queue survive the restart.

The deploy reloads `backend/content/`. That overwrites admin-console edits to the 75 problems that come from those files. Problems created in the console are left alone. Make lasting changes to the built-in problems in the content files.

## Settings

All settings live in `.env`. Run `./scripts/deploy.sh` again after changing one.

| Setting | Default | What it does |
|---|---|---|
| `DOMAIN` | (required) | The site's address. Caddy gets the certificate for it. |
| `WORKERS` | `2` | Submissions judged at the same time. About one per 0.5 vCPU. |
| `API_WORKERS` | `2` | API processes. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | How long a sign-in lasts (12 hours). |
| `SANDBOX_RUNTIME` | (empty) | Set to `runsc` to run user code under gVisor; see below. |

## Security

Already in place:

- **HTTPS everywhere:** automatic certificates, HSTS, and HTTP redirected to HTTPS.
- **Security headers:** `nosniff`, framing blocked, and a strict referrer policy.
- **Sandbox:** user code runs in a new container per test case with:
  - no network, 256 MB of memory, 1 CPU and at most 128 processes
  - a read-only filesystem
  - all capabilities dropped
  - an unprivileged user and a hard kill on timeout
- **Sign-in limits:** sign-in locks for 15 minutes after 10 failed attempts on one account, or 50 from one address.
- **Least privilege:** the API runs as a non-root user. Postgres and Redis aren't reachable from outside.
- **Hidden data:** hidden test cases are only ever sent to admins.

**Strongly recommended for a public site: gVisor.** The worker controls the host's Docker, and Docker containers share the host kernel. [gVisor](https://gvisor.dev) puts a user-space kernel between user code and the host. This is how many online judges and code playgrounds isolate untrusted code. To install it (Ubuntu, x86-64 or ARM):

```bash
curl -fsSL https://gvisor.dev/archive.key | sudo gpg --dearmor -o /usr/share/keyrings/gvisor-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gvisor-archive-keyring.gpg] https://storage.googleapis.com/gvisor/releases release main" \
  | sudo tee /etc/apt/sources.list.d/gvisor.list
sudo apt-get update && sudo apt-get install -y runsc
sudo runsc install && sudo systemctl restart docker
echo "SANDBOX_RUNTIME=runsc" >> .env && ./scripts/deploy.sh
```

Then submit a solution to check that it is still judged.

Also keep the server patched (`sudo apt-get update && sudo apt-get upgrade`, or enable `unattended-upgrades`), and use SSH keys rather than passwords.

## Monitoring

- **Health:** `https://<your-domain>/api/health` returns `{"status":"ok"}`. Point a free uptime monitor (such as UptimeRobot or Better Stack) at it.
- **Logs:** `docker compose -f docker-compose.prod.yml logs -f api worker web` shows them live. They're capped at 50 MB per service.
- **Status:** `docker compose -f docker-compose.prod.yml ps`.
- **API docs:** `https://<your-domain>/api/docs`.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Browser says the certificate is invalid, or the site won't load over HTTPS | DNS doesn't point at the server yet, or port 80 or 443 is blocked (check the cloud firewall too; on Oracle, both the security list and the server's iptables rules). See `docker compose -f docker-compose.prod.yml logs web`. |
| Every submission ends in **System Error** | The sandbox image is missing, or the worker can't reach Docker. Run `./scripts/deploy.sh` again and check `logs worker`. With `SANDBOX_RUNTIME=runsc`, check that `docker run --runtime=runsc hello-world` works. |
| Submissions stay "pending" | No worker is running. Check `ps` and `logs worker`. |
| "Too many failed sign-in attempts" | Wait 15 minutes, or clear it at once: `docker compose -f docker-compose.prod.yml exec redis redis-cli --scan --pattern 'login-failures:*' \| xargs -r docker compose -f docker-compose.prod.yml exec -T redis redis-cli del` |
