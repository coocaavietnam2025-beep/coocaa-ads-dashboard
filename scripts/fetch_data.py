#!/usr/bin/env python3
"""
Fetch daily performance data for the Meta Ads campaign "TV Khung Tranh Coocaa"
directly from the Meta Marketing (Graph) API and write it to data.json.

Runs inside GitHub Actions (see .github/workflows/update-data.yml).
Only uses the Python standard library — no pip install needed.

Required environment variables:
  META_ACCESS_TOKEN  - a Meta System User access token with ads_read on the account
  AD_ACCOUNT_ID      - numeric ad account id, e.g. 1623969776402359 (no "act_" prefix)
  CAMPAIGN_ID        - numeric campaign id, e.g. 120246939599090259
"""
import os
import sys
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error

GRAPH_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

ACCESS_TOKEN = os.environ["META_ACCESS_TOKEN"]
AD_ACCOUNT_ID = os.environ["AD_ACCOUNT_ID"].replace("act_", "")
CAMPAIGN_ID = os.environ["CAMPAIGN_ID"]


def call(path, params):
    params = dict(params)
    params["access_token"] = ACCESS_TOKEN
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTP error calling {path}: {body}", file=sys.stderr)
        raise


def get_action_value(actions, keyword):
    if not actions:
        return 0.0
    for a in actions:
        if keyword in a.get("action_type", ""):
            try:
                return float(a["value"])
            except (KeyError, ValueError):
                pass
    return 0.0


def empty_metrics():
    return {
        "spend": 0.0, "impressions": 0, "reach": 0, "clicks": 0,
        "ctr": 0.0, "cpm": 0.0, "cpc": 0.0, "frequency": 0.0,
        "results": 0.0, "cost_per_result": 0.0,
        "date_start": None, "date_stop": None,
    }


def insights_row_to_dict(row):
    if not row:
        return empty_metrics()
    actions = row.get("actions", [])
    spend = float(row.get("spend", 0) or 0)
    results = get_action_value(actions, "messaging_conversation_started")
    return {
        "spend": spend,
        "impressions": int(row.get("impressions", 0) or 0),
        "reach": int(row.get("reach", 0) or 0),
        "clicks": int(row.get("clicks", 0) or 0),
        "ctr": float(row.get("ctr", 0) or 0),
        "cpm": float(row.get("cpm", 0) or 0),
        "cpc": float(row.get("cpc", 0) or 0),
        "frequency": float(row.get("frequency", 0) or 0),
        "results": results,
        "cost_per_result": (spend / results) if results else 0.0,
        "date_start": row.get("date_start"),
        "date_stop": row.get("date_stop"),
    }


def main():
    today = datetime.date.today().isoformat()

    campaign = call(CAMPAIGN_ID, {
        "fields": "id,name,status,effective_status,objective,created_time"
    })
    since = (campaign.get("created_time") or today)[:10]
    time_range = json.dumps({"since": since, "until": today})
    insight_fields = "spend,impressions,reach,clicks,ctr,cpm,cpc,frequency,actions"

    adsets = call(f"{CAMPAIGN_ID}/adsets", {
        "fields": "id,name,status,effective_status,daily_budget,optimization_goal",
        "limit": 50,
    }).get("data", [])

    ads = call(f"{CAMPAIGN_ID}/ads", {
        "fields": "id,name,status,effective_status,adset_id,creative{id,name,thumbnail_url,image_url,body}",
        "limit": 50,
    }).get("data", [])

    campaign_rows = call(f"{CAMPAIGN_ID}/insights", {
        "level": "campaign", "fields": insight_fields, "time_range": time_range,
    }).get("data", [])

    adset_rows = call(f"{CAMPAIGN_ID}/insights", {
        "level": "adset", "fields": "adset_id," + insight_fields, "time_range": time_range,
    }).get("data", [])

    ad_rows = call(f"{CAMPAIGN_ID}/insights", {
        "level": "ad", "fields": "ad_id," + insight_fields, "time_range": time_range,
    }).get("data", [])

    daily_rows = call(f"{CAMPAIGN_ID}/insights", {
        "level": "campaign", "fields": insight_fields, "time_range": time_range, "time_increment": 1,
    }).get("data", [])

    adset_metrics_by_id = {r["adset_id"]: insights_row_to_dict(r) for r in adset_rows}
    ad_metrics_by_id = {r["ad_id"]: insights_row_to_dict(r) for r in ad_rows}

    out_adsets = [{**a, "metrics": adset_metrics_by_id.get(a["id"], empty_metrics())} for a in adsets]

    out_ads = []
    for a in ads:
        creative = a.get("creative") or {}
        out_ads.append({
            "id": a["id"],
            "name": a["name"],
            "status": a["status"],
            "effective_status": a.get("effective_status"),
            "adset_id": a.get("adset_id"),
            "creative": {
                "id": creative.get("id"),
                "name": creative.get("name"),
                "image": creative.get("thumbnail_url") or creative.get("image_url"),
                "body": creative.get("body"),
            },
            "metrics": ad_metrics_by_id.get(a["id"], empty_metrics()),
        })

    output = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "campaign": {
            "id": campaign["id"],
            "name": campaign["name"],
            "status": campaign["status"],
            "effective_status": campaign.get("effective_status"),
            "objective": campaign.get("objective"),
            "metrics": insights_row_to_dict(campaign_rows[0] if campaign_rows else None),
        },
        "adsets": out_adsets,
        "ads": out_ads,
        "daily": [insights_row_to_dict(r) for r in daily_rows],
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Wrote data.json for campaign:", output["campaign"]["name"])


if __name__ == "__main__":
    main()
