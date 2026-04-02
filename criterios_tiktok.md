solicitud:
```python
from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient("<YOUR_API_TOKEN>")

# Prepare the Actor input
run_input = {
    "excludePinnedPosts": False,
    "profiles": ["apifyoffice"], # tiktok_username only
    "profileSorting": "latest",   
    "resultsPerPage": 1,
    "shouldDownloadAvatars": False,
    "shouldDownloadCovers": False,
    "shouldDownloadSlideshowImages": False,
    "shouldDownloadSubtitles": False,
    "shouldDownloadVideos": False
}

# Run the Actor and wait for it to finish
run = client.actor("0FXVyOXXEmdGcV88a").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

result:

```json
[
  {
    "id": "7623046776752295175",
    "text": "Basta de abrir el baúl y que todo esté tirado 👀\nOrganizá TODO en un solo lugar con este maletín para tu auto ✔️ Práctico, compacto y súper cómodo de llevar.\n\nConseguilo en Oh my Shop ~ Juan B. Justo 5038, CABA 🩷",
    "textLanguage": "es",
    "createTime": 1774878892,
    "createTimeISO": "2026-03-30T13:54:52.000Z",
    "isAd": false,
    "authorMeta": {
      "id": "6824909367272768518",
      "name": "ohmyshop.store",
      "profileUrl": "https://www.tiktok.com/@ohmyshop.store",
      "nickName": "Oh My Shop!",
      "verified": false,
      "signature": "Tienda on line- 🇦🇷\nEstamos en Juan B Justo 5038\n www.ohmyshop.com.ar",
      "bioLink": "https://tienda.ohmyshop.com.ar",
      "avatar": "https://p16-common-sign.tiktokcdn-us.com/tos-maliva-avt-0068/b40a9b6e8ad8b21873fcee3301be89c9~tplv-tiktokx-cropcenter:720:720.jpeg?dr=9640&refresh_token=717029a2&x-expires=1775059200&x-signature=xQENVlXNHw5fRma%2FubMHQHiNfeY%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5",
      "commerceUserInfo": {
        "commerceUser": true,
        "category": "Shopping & Retail",
        "categoryButton": false
      },
      "privateAccount": false,
      "roomId": "",
      "ttSeller": false,
      "createTime": 1589020094,
      "following": 204,
      "friends": 13,
      "fans": 1982,
      "heart": 8422,
      "video": 148,
      "digg": 231,
      "originalAvatarUrl": "https://p16-common-sign.tiktokcdn-us.com/tos-maliva-avt-0068/b40a9b6e8ad8b21873fcee3301be89c9~tplv-tiktokx-cropcenter:720:720.jpeg?dr=9640&refresh_token=717029a2&x-expires=1775059200&x-signature=xQENVlXNHw5fRma%2FubMHQHiNfeY%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5"
    },
    "musicMeta": {
      "musicName": "sonido original",
      "musicAuthor": "Oh My Shop!",
      "musicOriginal": true,
      "playUrl": "https://v16m.tiktokcdn-us.com/a01b23c0c49bc62009b4d1c514921e8c/69cafbda/video/tos/alisg/tos-alisg-v-27dcd7/ogLQBGlbMEgdCuGocDgI4oFqEIrTAKLfTKCeHe/?a=1233&bti=ODszNWYuMDE6&ch=0&cr=0&dr=0&er=0&lr=default&cd=0%7C0%7C0%7C0&br=250&bt=125&ft=GSDrKInz7ThITXXPXq8Zmo&mime_type=audio_mpeg&qs=6&rc=aWgzNDo1aGc6OTs4OzhlZkBpamh4ZXE5cmU7OjMzODU8NEA2Yl5iLjY0NTMxMzE0LWM2YSMwZW8tMmRrLjJhLS1kMS1zcw%3D%3D&vvpl=1&l=2026033016395945F26C0E4B0C4B164C7F&btag=e000b8000",
      "coverMediumUrl": "https://p16-common-sign.tiktokcdn-us.com/tos-maliva-avt-0068/b40a9b6e8ad8b21873fcee3301be89c9~tplv-tiktokx-cropcenter:720:720.jpeg?dr=9640&refresh_token=717029a2&x-expires=1775059200&x-signature=xQENVlXNHw5fRma%2FubMHQHiNfeY%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5",
      "musicId": "7623046815311923988",
      "originalCoverMediumUrl": "https://p16-common-sign.tiktokcdn-us.com/tos-maliva-avt-0068/b40a9b6e8ad8b21873fcee3301be89c9~tplv-tiktokx-cropcenter:720:720.jpeg?dr=9640&refresh_token=717029a2&x-expires=1775059200&x-signature=xQENVlXNHw5fRma%2FubMHQHiNfeY%3D&t=4d5b0474&ps=13740610&shp=a5d48078&shcp=81f88b70&idc=useast5"
    },
    "webVideoUrl": "https://www.tiktok.com/@ohmyshop.store/video/7623046776752295175",
    "videoMeta": {
      "height": 1024,
      "width": 576,
      "duration": 27,
      "coverUrl": "https://p16-common-sign.tiktokcdn-us.com/tos-alisg-p-0037/ooK3EKFrAmUqwf4KBADAICyhR4pggCDEAoEqfo~tplv-tiktokx-origin.image?dr=9636&x-expires=1775059200&x-signature=LJWTIgqu2wvTDfLwTdVSCow6lzM%3D&t=4d5b0474&ps=13740610&shp=81f88b70&shcp=43f4a2f9&idc=useast5",
      "definition": "540p",
      "format": "mp4",
      "subtitleLinks": [
        {
          "language": "spa-ES",
          "downloadLink": "https://v16m-webapp.tiktokcdn-us.com/2139c3a3d481e2d15ce666c5dfa1075b/69cd4a7a/video/tos/alisg/tos-alisg-pv-0037/e852aa7838f443b1bdc3b6036a6e6a2e/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C&cv=1&br=29868&bt=14934&ds=4&ft=4KLMeMzm8Zmo0qo44x4jVKRbdpWrKsd.&mime_type=video_mp4&qs=13&rc=anI6cHA5cnc7OjMzODczNEBpanI6cHA5cnc7OjMzODczNEA2NnIvMmRrLTJhLS1kMTFzYSM2NnIvMmRrLTJhLS1kMTFzcw%3D%3D&l=2026033016395945F26C0E4B0C4B164C7F&btag=e00078000",
          "source": "ASR",
          "sourceUnabbreviated": "automatic speech recognition",
          "version": "1:whisper_lid",
          "tiktokLink": "https://v16m-webapp.tiktokcdn-us.com/2139c3a3d481e2d15ce666c5dfa1075b/69cd4a7a/video/tos/alisg/tos-alisg-pv-0037/e852aa7838f443b1bdc3b6036a6e6a2e/?a=1988&bti=ODszNWYuMDE6&ch=0&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C&cv=1&br=29868&bt=14934&ds=4&ft=4KLMeMzm8Zmo0qo44x4jVKRbdpWrKsd.&mime_type=video_mp4&qs=13&rc=anI6cHA5cnc7OjMzODczNEBpanI6cHA5cnc7OjMzODczNEA2NnIvMmRrLTJhLS1kMTFzYSM2NnIvMmRrLTJhLS1kMTFzcw%3D%3D&l=2026033016395945F26C0E4B0C4B164C7F&btag=e00078000"
        }
      ],
      "transcriptionLink": null,
      "originalCoverUrl": "https://p16-common-sign.tiktokcdn-us.com/tos-alisg-p-0037/ooK3EKFrAmUqwf4KBADAICyhR4pggCDEAoEqfo~tplv-tiktokx-origin.image?dr=9636&x-expires=1775059200&x-signature=LJWTIgqu2wvTDfLwTdVSCow6lzM%3D&t=4d5b0474&ps=13740610&shp=81f88b70&shcp=43f4a2f9&idc=useast5"
    },
    "diggCount": 4,
    "shareCount": 0,
    "playCount": 165,
    "collectCount": 0,
    "commentCount": 0,
    "repostCount": 0,
    "mentions": [],
    "detailedMentions": [],
    "hashtags": [],
    "effectStickers": [],
    "isSlideshow": false,
    "isPinned": false,
    "isSponsored": false,
    "mediaUrls": [],
    "input": "ohmyshop.store",
    "fromProfileSection": "videos",
    "commentsDatasetUrl": null
  },
]
```
Engagement: ((Likes + Comentarios + Shares) ÷ Seguidores) × 100

Mismo criterio de puntos que instagram