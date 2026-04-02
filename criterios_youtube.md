get info de Google Youtube Data API V3
```python
# -*- coding: utf-8 -*-

# Sample Python code for youtube.channels.list
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

from googleapiclient.discovery import build


scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    request = youtube.channels().list(
        part="snippet, statistics, status, topicDetails, contentDetails",
        forUsername="youtube_channel_username" # if the url have the ID:  id="UCEUzE9r1n9t0hwHBP7QhxSg"
    )
    response = request.execute()

    print(response)

if __name__ == "__main__":
    main()
```

respuesta
```json
{
  "kind": "youtube#channelListResponse",
  "etag": "uL_IPDf_jvt8PVNXJs8YnuHExng",
  "pageInfo": {
    "totalResults": 1,
    "resultsPerPage": 5
  },
  "items": [
    {
      "kind": "youtube#channel",
      "etag": "3lqtk0ju_i1SIiQROSnM_HYxdNc",
      "id": "UCCkxMbfZ80VFwwiRlIG5P5g",
      "snippet": {
        "title": "FromSoftware, Inc.",
        "description": "株式会社フロム・ソフトウェアが運営する公式動画ライブラリーです。\nフロム・ソフトウェア作品の様々な映像を公開しています。随時更新中。\n\nThis page is Official movie library which FromSoftware, Inc. runs.\nI show various movies of the FromSoftware work. \nUnder occasional update.\n\nFromSoftware Official Account\n\n　X\n　　@fromsoftware_pr\n\n　facebook Page\n　　http://www.facebook.com/fromsoftware.jp\n\n　Instagram\n　　fromsoftware_jp",
        "customUrl": "@fromsoftwareinc",
        "publishedAt": "2008-11-21T12:24:18Z",
        "thumbnails": {
          "default": {
            "url": "https://yt3.ggpht.com/XV9vAzqRSayewtOK_t2vn0lWSOpv-n-I0NbN7v-m9K2dzkHJYlj8QrTt3KmjD6fzTiHD03FUnA=s88-c-k-c0x00ffffff-no-rj",
            "width": 88,
            "height": 88
          },
          "medium": {
            "url": "https://yt3.ggpht.com/XV9vAzqRSayewtOK_t2vn0lWSOpv-n-I0NbN7v-m9K2dzkHJYlj8QrTt3KmjD6fzTiHD03FUnA=s240-c-k-c0x00ffffff-no-rj",
            "width": 240,
            "height": 240
          },
          "high": {
            "url": "https://yt3.ggpht.com/XV9vAzqRSayewtOK_t2vn0lWSOpv-n-I0NbN7v-m9K2dzkHJYlj8QrTt3KmjD6fzTiHD03FUnA=s800-c-k-c0x00ffffff-no-rj",
            "width": 800,
            "height": 800
          }
        },
        "localized": {
          "title": "FromSoftware, Inc.",
          "description": "株式会社フロム・ソフトウェアが運営する公式動画ライブラリーです。\nフロム・ソフトウェア作品の様々な映像を公開しています。随時更新中。\n\nThis page is Official movie library which FromSoftware, Inc. runs.\nI show various movies of the FromSoftware work. \nUnder occasional update.\n\nFromSoftware Official Account\n\n　X\n　　@fromsoftware_pr\n\n　facebook Page\n　　http://www.facebook.com/fromsoftware.jp\n\n　Instagram\n　　fromsoftware_jp"
        },
        "country": "JP"
      },
      "contentDetails": {
        "relatedPlaylists": {
          "likes": "",
          "uploads": "UUCkxMbfZ80VFwwiRlIG5P5g"
        }
      },
      "statistics": {
        "viewCount": "52224034",
        "subscriberCount": "303000",
        "hiddenSubscriberCount": false,
        "videoCount": "160"
      },
      "topicDetails": {
        "topicIds": [
          "/m/02ntfj",
          "/m/025zzc",
          "/m/0bzvm2",
          "/m/0403l3g"
        ],
        "topicCategories": [
          "https://en.wikipedia.org/wiki/Action-adventure_game",
          "https://en.wikipedia.org/wiki/Action_game",
          "https://en.wikipedia.org/wiki/Video_game_culture",
          "https://en.wikipedia.org/wiki/Role-playing_video_game"
        ]
      },
      "status": {
        "privacyStatus": "public",
        "isLinked": true,
        "longUploadsStatus": "longUploadsUnspecified"
      }
    }
  ]
}
```

limpiar cateogria: topicCategories

engagement: ((Likes + Comentarios) ÷ Vistas del último video) × 100

```python
def get_latest_video_id(youtube, uploads_playlist_id: str) -> str | None:
    try:
        resp = (
            youtube.playlistItems()
            .list(part="contentDetails", playlistId=uploads_playlist_id, maxResults=1)
            .execute()
        )
        time.sleep(REQUEST_DELAY)
        items = resp.get("items", [])
        if not items:
            return None
        return (
            items[0]
            .get("contentDetails", {})
            .get("videoId")
        )
    except Exception as e:
        print(f"  playlistItems: {e}")
        time.sleep(REQUEST_DELAY)
        return None

def normalize_video_statistics(raw: dict) -> dict:
    """Alinea con el formato esperado (strings); dislike suele faltar en la API."""
    keys = (
        "viewCount",
        "likeCount",
        "dislikeCount",
        "favoriteCount",
        "commentCount",
    )
    out = {}
    for k in keys:
        v = raw.get(k)
        out[k] = str(v) if v is not None else "0"
    return out


def fetch_latest_video_statistics(
    youtube, uploads_playlist_id: str | None
) -> tuple[dict | None, dict]:
    """
    Devuelve (statistics_normalizado, meta) donde meta incluye videoId y título si hay.
    """
    uploads = uploads_playlist_id
    if not uploads:
        return None, {"error": "sin playlist de uploads"}
    vid = get_latest_video_id(youtube, uploads)
    if not vid:
        return None, {"error": "sin vídeos en el canal"}
    try:
        resp = (
            youtube.videos()
            .list(part="statistics,snippet", id=vid)
            .execute()
        )
        time.sleep(REQUEST_DELAY)
        items = resp.get("items", [])
        if not items:
            return None, {"error": "vídeo no encontrado", "videoId": vid}
        item = items[0]
        stats = item.get("statistics") or {}
        snippet = item.get("snippet") or {}
        meta = {
            "videoId": vid,
            "title": snippet.get("title", ""),
            "publishedAt": snippet.get("publishedAt", ""),
        }
        return normalize_video_statistics(stats), meta
    except Exception as e:
        time.sleep(REQUEST_DELAY)
        return None, {"error": str(e), "videoId": vid}
```

puntuacion de puntos igual que las anteriores