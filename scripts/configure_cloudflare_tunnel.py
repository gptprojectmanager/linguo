#!/usr/bin/env python3
"""
Automated Cloudflare Zero Trust Ingress & DNS Configuration for Linguo
Binds `linguo.princyx.xyz` -> `http://localhost:8765` on tunnel `home-recovery`.
Usage:
    dotenvx run -- python3 scripts/configure_cloudflare_tunnel.py
    # or with env vars:
    CLOUDFLARE_API_TOKEN=... python3 scripts/configure_cloudflare_tunnel.py
"""

import os
import sys
import json
import urllib.request
import urllib.error

TUNNEL_ID = "136e6875-c047-4b95-a84a-bdc9d9fbb771"  # home-recovery tunnel on Dell 7670
HOSTNAME = "linguo.princyx.xyz"
ZONE_NAME = "princyx.xyz"
TARGET_SERVICE = "http://localhost:8765"
CF_API_BASE = "https://api.cloudflare.com/client/v4"


def get_token() -> str:
    token = (
        os.environ.get("CLOUDFLARE_API_TOKEN")
        or os.environ.get("CF_API_TOKEN")
        or os.environ.get("CLOUDFLARE_TOKEN")
        or os.environ.get("CF_TOKEN")
    )
    if not token:
        print("\033[1;31m❌ Errore: Nessun token Cloudflare trovato nell'ambiente.\033[0m")
        print("Assicurati di lanciare il comando con dotenvx:")
        print("  \033[1;36mdotenvx run -- python3 scripts/configure_cloudflare_tunnel.py\033[0m")
        print("oppure esporta CLOUDFLARE_API_TOKEN=...")
        sys.exit(1)
    return token.strip()


def cf_request(url: str, token: str, method: str = "GET", data: dict = None) -> dict:
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        print(f"\033[1;31mHTTP Error {e.code} on {method} {url}:\033[0m\n{err_body}")
        raise
    except Exception as e:
        print(f"\033[1;31mRequest Error on {method} {url}: {e}\033[0m")
        raise


def get_account_id(token: str) -> str:
    acc_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID")
    if acc_id:
        return acc_id.strip()

    print("🔍 Ricerca account Cloudflare associato al token...")
    res = cf_request(f"{CF_API_BASE}/accounts", token)
    accounts = res.get("result", [])
    if not accounts:
        raise RuntimeError("Nessun account Cloudflare accessibile con questo token.")
    account_id = accounts[0]["id"]
    print(f"  • Account rilevato: \033[1;32m{accounts[0].get('name', 'N/A')}\033[0m (ID: {account_id})")
    return account_id


def get_zone_id(token: str, zone_name: str) -> str:
    print(f"🔍 Ricerca zone DNS per '{zone_name}'...")
    res = cf_request(f"{CF_API_BASE}/zones?name={zone_name}", token)
    zones = res.get("result", [])
    if not zones:
        raise RuntimeError(f"Zona DNS '{zone_name}' non trovata per questo account.")
    zone_id = zones[0]["id"]
    print(f"  • Zone ID: \033[1;32{zone_id}\033[0m")
    return zone_id


def configure_tunnel_ingress(token: str, account_id: str):
    print(f"\n🚇 Configurazione Ingress Tunnel: \033[1;33m{TUNNEL_ID}\033[0m...")
    url = f"{CF_API_BASE}/accounts/{account_id}/cfd_tunnel/{TUNNEL_ID}/configurations"

    try:
        curr = cf_request(url, token, method="GET")
        config = curr.get("result", {}).get("config", {})
    except Exception as e:
        print(f"⚠️ Impossibile leggere configurazione esistente, creazione nuova: {e}")
        config = {}

    ingress = config.get("ingress", [])

    # Check if route already exists
    updated = False
    new_ingress = []
    catch_all = None

    for rule in ingress:
        service = rule.get("service", "")
        hostname = rule.get("hostname", "")

        # Catch-all rule (no hostname or http_status:404)
        if not hostname or "http_status" in service:
            catch_all = rule
            continue

        if hostname == HOSTNAME:
            print(f"  • Aggiornamento regola esistente per {HOSTNAME} -> {TARGET_SERVICE}")
            new_ingress.append({"hostname": HOSTNAME, "service": TARGET_SERVICE})
            updated = True
        else:
            new_ingress.append(rule)

    if not updated:
        print(f"  • Aggiunta nuova regola: \033[1;32m{HOSTNAME} -> {TARGET_SERVICE}\033[0m")
        new_ingress.append({"hostname": HOSTNAME, "service": TARGET_SERVICE})

    # Always ensure catch-all is at the very end
    if catch_all:
        new_ingress.append(catch_all)
    else:
        new_ingress.append({"service": "http_status:404"})

    config["ingress"] = new_ingress
    payload = {"config": config}

    put_res = cf_request(url, token, method="PUT", data=payload)
    if put_res.get("success"):
        print("  ✅ Ingress Cloudflare Tunnel salvato con successo!")
    else:
        print(f"  ❌ Errore aggiornamento ingress: {put_res.get('errors')}")


def configure_dns_record(token: str, zone_id: str):
    print(f"\n🌐 Verifica record DNS per \033[1;33m{HOSTNAME}\033[0m...")
    cname_target = f"{TUNNEL_ID}.cfargotunnel.com"

    records_res = cf_request(f"{CF_API_BASE}/zones/{zone_id}/dns_records?name={HOSTNAME}", token)
    records = records_res.get("result", [])

    if records:
        rec = records[0]
        rec_id = rec["id"]
        if rec.get("content") == cname_target and rec.get("proxied") is True:
            print(f"  ✅ Record DNS CNAME già correttamente configurato e proxied ({cname_target}).")
            return

        print(f"  • Aggiornamento record DNS {rec_id} -> CNAME {cname_target} (proxied)...")
        payload = {
            "type": "CNAME",
            "name": "linguo",
            "content": cname_target,
            "proxied": True,
            "ttl": 1
        }
        cf_request(f"{CF_API_BASE}/zones/{zone_id}/dns_records/{rec_id}", token, method="PUT", data=payload)
        print("  ✅ Record DNS CNAME aggiornato con successo!")
    else:
        print(f"  • Creazione nuovo record DNS CNAME {HOSTNAME} -> {cname_target} (proxied)...")
        payload = {
            "type": "CNAME",
            "name": "linguo",
            "content": cname_target,
            "proxied": True,
            "ttl": 1
        }
        cf_request(f"{CF_API_BASE}/zones/{zone_id}/dns_records", token, method="POST", data=payload)
        print("  ✅ Record DNS CNAME creato con successo!")


def test_endpoint():
    print(f"\n🩺 Verifica Probe Remoto via HTTPS: https://{HOSTNAME}/health ...")
    try:
        req = urllib.request.Request(f"https://{HOSTNAME}/health")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  🎉 \033[1;32mONLINE! HTTP 200 OK\033[0m -> {data}")
    except Exception as e:
        print(f"  ⏳ Nota: La propagazione DNS/Cloudflare può richiedere 30-60 secondi. Dettaglio: {e}")


def main():
    print("\033[1;36m=====================================================\033[0m")
    print("\033[1;36m   Linguo Cloudflare Tunnel Automator (Tier 2 Ingress) \033[0m")
    print("\033[1;36m=====================================================\033[0m")
    token = get_token()
    account_id = get_account_id(token)
    zone_id = get_zone_id(token, ZONE_NAME)

    configure_tunnel_ingress(token, account_id)
    configure_dns_record(token, zone_id)
    test_endpoint()


if __name__ == "__main__":
    main()
