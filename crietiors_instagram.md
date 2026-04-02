from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)

# Prepare the Actor input
run_input = {
    "directUrls": ["https://www.instagram.com/humansofny/"],
    "resultsType": "posts",
    "resultsLimit": 200,
    "onlyPostsNewerThan": None,
    "search": None,
    "searchType": "hashtag",
    "searchLimit": 1,
    "addParentData": False,
}

# Run the Actor and wait for it to finish
run = client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)

  {
    "inputUrl": "https://www.instagram.com/holdnstorage",
    "id": "69820043835",
    "username": "holdnstorage",
    "url": "https://www.instagram.com/holdnstorage",
    "fullName": "Hold N Storage",
    "biography": "🏠 Organizing Made Easy\n🛒 Find Storage Solutions for Every Room\n✨ Transform Clutter into Comfort\n📲 Shop Now: holdnstorage.com",
    "externalUrls": [],
    "followersCount": 14,
    "followsCount": 0,
    "hasChannel": false,
    "highlightReelCount": 0,
    "isBusinessAccount": true,
    "joinedRecently": false,
    "businessCategoryName": "None",
    "private": false,
    "verified": false,
    "profilePicUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-19/465277706_3713961318857959_6349861368021081503_n.jpg?stp=dst-jpg_e0_s150x150_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=107&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=TLvk_SI3A8YQ7kNvwF2TSKA&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AfwyC-c6zf2OQ8L_4E934Wsl8pZOaL5voGu9b1x7x8NlZQ&oe=69D06524&_nc_sid=8b3546",
    "profilePicUrlHD": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-19/465277706_3713961318857959_6349861368021081503_n.jpg?stp=dst-jpg_s320x320_tt6&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLmRqYW5nby4xMDgwLmMyIn0&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=107&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=TLvk_SI3A8YQ7kNvwF2TSKA&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_Afzftih8Vgk4rncr1LGgCOCr75FDs1h3E_k_qIqN-y-JEg&oe=69D06524&_nc_sid=8b3546",
    "igtvVideoCount": 0,
    "relatedProfiles": [],
    "latestIgtvVideos": [],
    "postsCount": 7,
    "latestPosts": [
      {
        "id": "3648513426424823967",
        "type": "Image",
        "shortCode": "DKiH6F0S4Cf",
        "caption": "Celebrate the dads who do it all!\nUse code DAD20 to get 20% OFF orders over $30.\n💙 A little extra love (and storage) this Father’s Day.\n👇 Shop now!\nhttps://holdnstorage.com\n\n#FathersDay #FathersDayGift #DadsRule #HomeOrganization #StorageSolutions #FathersDaySale #DiscountCode #HoldnStorage",
        "hashtags": [
          "FathersDay",
          "FathersDayGift",
          "DadsRule",
          "HomeOrganization",
          "StorageSolutions",
          "FathersDaySale",
          "DiscountCode",
          "HoldnStorage"
        ],
        "mentions": [],
        "url": "https://www.instagram.com/p/DKiH6F0S4Cf/",
        "commentsCount": 0,
        "dimensionsHeight": 1080,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/503927912_17880079548323836_4435967375563582098_n.jpg?stp=dst-jpg_e15_fr_s1080x1080_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=eDX0kjPyh14Q7kNvwFZ8sX6&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&ig_cache_key=MzY0ODUxMzQyNjQyNDgyMzk2Nw%3D%3D.3-ccb7-5&oh=00_Afyo-ZwYQfFv9EkSZSS_0dtH-6a4pyL7dSSbbUUzSUzI6w&oe=69D08EE4&_nc_sid=8b3546",
        "images": [],
        "alt": "Photo by Hold N Storage on June 05, 2025.",
        "likesCount": 1,
        "timestamp": "2025-06-05T20:51:55.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "isCommentsDisabled": false
      },
      {
        "id": "3641215586739288723",
        "type": "Video",
        "shortCode": "DKIMki-NfqT",
        "caption": "Taking time this Memorial Day to refresh your space? Try this simple cabinet organizer solution that makes your home feel instantly lighter.\n\n Appreciating the little things.\n\n#MemorialDayWeekend #HomeOrganization #CabinetMakeover #OrganizedLife #DeclutterYourHome #HomeHacks #BeforeAndAfter #Holdnstorage",
        "hashtags": [
          "MemorialDayWeekend",
          "HomeOrganization",
          "CabinetMakeover",
          "OrganizedLife",
          "DeclutterYourHome",
          "HomeHacks",
          "BeforeAndAfter",
          "Holdnstorage"
        ],
        "mentions": [],
        "url": "https://www.instagram.com/p/DKIMki-NfqT/",
        "commentsCount": 0,
        "dimensionsHeight": 1921,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/501453846_17878825995323836_2281023910952443700_n.jpg?stp=dst-jpg_e35_p1080x1080_sh0.08_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=lJA_ZtCFWd8Q7kNvwEKb5HU&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AfzUYvqbQB12lNODD4iFkS9WqarnSx4AostbnK6TQP8OYA&oe=69D07A8C&_nc_sid=8b3546",
        "images": [],
        "videoUrl": "https://scontent-ord5-1.cdninstagram.com/o1/v/t2/f2/m367/AQM_501Op_TrBttN79F4mSLbUvB24reGbM8OOE0QWPliJeN5KSR49VPbi7nKksYbUyUU6vRw21Av_9Gm8Ws08b9qBFcMG0gwxBOoMkQ.mp4?_nc_cat=101&_nc_sid=5e9851&_nc_ht=scontent-ord5-1.cdninstagram.com&_nc_ohc=qpH1YFz4ZQwQ7kNvwErIpwU&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuNzIwLmRhc2hfYmFzZWxpbmVfMV92MSIsInhwdl9hc3NldF9pZCI6MTA2NDE5Mjk3NTYwNTA4NCwiYXNzZXRfYWdlX2RheXMiOjMwNywidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjIxLCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=a7b2154e7dc71b42&_nc_vs=HBksFQIYQGlnX2VwaGVtZXJhbC9GNTQ5MTM3NUUwMkM0NDkxMjA3QUYwNUU1NDNEMkJBOF92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYRmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC81Nzc3NjA4MTIwNDU5ODNfNDU3NTU1NDA2MTk3NTUxMzI1Ni5tcDQVAgLIARIAKAAYABsCiAd1c2Vfb2lsATEScHJvZ3Jlc3NpdmVfcmVjaXBlATEVAAAmuLXExJf44wMVAigCQzMsF0A1Kn752yLRGBJkYXNoX2Jhc2VsaW5lXzFfdjERAHX-B2XmnQEA&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&_nc_ss=7a3ba&_nc_zt=28&oh=00_AfwmyiDOe2JmsCc83p-Ex_pxB2Ze0sHt5pJ-LrNWEU5K_g&oe=69D07D66",
        "alt": null,
        "likesCount": 2,
        "videoViewCount": 4,
        "timestamp": "2025-05-26T19:12:41.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "productType": "clips",
        "isCommentsDisabled": false
      },
      {
        "id": "3636179641217769812",
        "type": "Image",
        "shortCode": "DJ2Th5OSuFU",
        "caption": "Memorial Day SALE starts now!\n\nGet 25% OFF all orders over $100 with code HEROES25 💥\n\n🛒 Shop now 👉 holdnstorage.com\n📆 Limited-time offer — get your favorites before they’re gone!\n\n#MemorialDaySale #HoldnStorage #OrganizeYourHome #HolidayDeals #HEROES25",
        "hashtags": [
          "MemorialDaySale",
          "HoldnStorage",
          "OrganizeYourHome",
          "HolidayDeals",
          "HEROES25"
        ],
        "mentions": [],
        "url": "https://www.instagram.com/p/DJ2Th5OSuFU/",
        "commentsCount": 0,
        "dimensionsHeight": 1080,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/499704342_17877906687323836_5590948539769505585_n.jpg?stp=dst-jpg_e35_s1080x1080_sh0.08_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=A_TFTQdllxAQ7kNvwEVrvOV&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&ig_cache_key=MzYzNjE3OTY0MTIxNzc2OTgxMg%3D%3D.3-ccb7-5&oh=00_AfzK-c9q8bxVwsq79r_SQi_ZnOWbe3lL7D_PM7D1k07Ylg&oe=69D0857F&_nc_sid=8b3546",
        "images": [],
        "alt": "Photo by Hold N Storage on May 19, 2025.",
        "likesCount": 2,
        "timestamp": "2025-05-19T20:26:53.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "isCommentsDisabled": false
      },
      {
        "id": "3626035699553674377",
        "type": "Image",
        "shortCode": "DJSREHWyCSJ",
        "caption": "🌸 Mother’s Day SALE! 🌸\nCelebrate Mom (or treat yourself!) with 20% off orders over $30.\n✨ Use code MOM20 at checkout.\n💗 Hurry — offer valid through 5/13/25!\n\nShop now 👉 www.holdnstorage.com\n#MothersDay #Sale #MothersDayGift #HoldnStorage #MomLove",
        "hashtags": [
          "MothersDay",
          "Sale",
          "MothersDayGift",
          "HoldnStorage",
          "MomLove"
        ],
        "mentions": [],
        "url": "https://www.instagram.com/p/DJSREHWyCSJ/",
        "commentsCount": 2,
        "dimensionsHeight": 1080,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/495492711_17876173155323836_1064381047978350929_n.jpg?stp=dst-jpg_e15_fr_s1080x1080_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=S6gpj6EoFIIQ7kNvwFqkvHG&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&ig_cache_key=MzYyNjAzNTY5OTU1MzY3NDM3Nw%3D%3D.3-ccb7-5&oh=00_Afy9_11-mSfxMfU47s-V2V7UAjhsDQOEHYUpwoujM00WEQ&oe=69D08FBE&_nc_sid=8b3546",
        "images": [],
        "alt": "Photo by Hold N Storage on May 05, 2025.",
        "likesCount": 2,
        "timestamp": "2025-05-05T20:32:41.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "isCommentsDisabled": false
      },
      {
        "id": "3623714481784610516",
        "type": "Image",
        "shortCode": "DJKBR82Nd7U",
        "caption": "Seal, pack, picnic! 🌿\n\nFresh, leak-free snacks with our vacuum-sealed containers — the perfect companion for all your spring outdoor adventures.\n\n👉 Shop now: www.holdnstorage.com\n\n#SpringPicnic #PicnicReady #VacuumSealed #FreshSnacks #LeakproofContainers #HoldnStorage",
        "hashtags": [
          "SpringPicnic",
          "PicnicReady",
          "VacuumSealed",
          "FreshSnacks",
          "LeakproofContainers",
          "HoldnStorage"
        ],
        "mentions": [],
        "url": "https://www.instagram.com/p/DJKBR82Nd7U/",
        "commentsCount": 0,
        "dimensionsHeight": 1080,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/495342176_17875776267323836_3869569084308956369_n.jpg?stp=dst-jpg_e15_fr_s1080x1080_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=0j_Dw1rREQAQ7kNvwE4s8MW&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&ig_cache_key=MzYyMzcxNDQ4MTc4NDYxMDUxNg%3D%3D.3-ccb7-5&oh=00_AfyOiMQd5JUItYyA0msdpp2aQer0MrBQSBfLOwh6SB_QMQ&oe=69D085DB&_nc_sid=8b3546",
        "images": [],
        "alt": "Photo by Hold N Storage on May 02, 2025.",
        "likesCount": 1,
        "timestamp": "2025-05-02T15:40:50.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "isCommentsDisabled": false
      },
      {
        "id": "3552014884520300834",
        "type": "Image",
        "shortCode": "DFLSrfUu5Ei",
        "caption": "Get yours today! \n\nhttps://www.holdnstorage.com/products/pull-out-organizer-for-cookie-sheet-cutting-board-bakeware-and-tray-sliding-rack-heavy-duty-5-year-limited-warranty-for-under-sink-under-cabinet-chrome?_pos=1&_sid=692477e43&_ss=r",
        "hashtags": [],
        "mentions": [],
        "url": "https://www.instagram.com/p/DFLSrfUu5Ei/",
        "commentsCount": 0,
        "dimensionsHeight": 1080,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/474590264_17863061577323836_3716732572924489505_n.jpg?stp=dst-jpg_e35_s1080x1080_sh0.08_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=t74ztJkdBO4Q7kNvwHVuWEu&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&ig_cache_key=MzU1MjAxNDg4NDUyMDMwMDgzNA%3D%3D.3-ccb7-5&oh=00_AfwXKbfJ2ilpjgJQQf3xmmsNWvvfreoHMHQLC0U2h_d9Zg&oe=69D083F3&_nc_sid=8b3546",
        "images": [],
        "alt": "Photo by Hold N Storage on January 23, 2025.",
        "likesCount": 1,
        "timestamp": "2025-01-23T17:26:32.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "isCommentsDisabled": false
      },
      {
        "id": "3506404043448599984",
        "type": "Video",
        "shortCode": "DCpP-ZYv0Ww",
        "caption": "Get organized with Hold N Storage this holiday season! \n\nhttps://www.holdnstorage.com/",
        "hashtags": [],
        "mentions": [],
        "url": "https://www.instagram.com/p/DCpP-ZYv0Ww/",
        "commentsCount": 0,
        "dimensionsHeight": 607,
        "dimensionsWidth": 1080,
        "displayUrl": "https://scontent-ord5-3.cdninstagram.com/v/t51.2885-15/467893654_17854211403323836_56545931971097432_n.jpg?stp=dst-jpg_e35_s1080x1080_sh0.08_tt6&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_cat=104&_nc_oc=Q6cZ2gHZvg2REuJI23v-mWvrfKlK3jrx8_1Snz88DALlB7LOAVzouMzq4u4Fm2C4G1XmFYY&_nc_ohc=2ntlkB_dRNAQ7kNvwFfp4y2&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&edm=AOQ1c0wBAAAA&ccb=7-5&oh=00_AfzGjqWpoq1TxhwMhDlpNEnrUT4_IOGt9ICIV2GYcEbTrQ&oe=69D07ECC&_nc_sid=8b3546",
        "images": [],
        "videoUrl": "https://scontent-ord5-3.cdninstagram.com/o1/v/t2/f2/m367/AQOz87m-9sBXkkhgqcJrW6MYiXTMs7p5hgci8t3pcf0R2iTbNPVSrd-vf-10rZ7t9svkUoq0mGu9KZmg4s-d3j3x_4O3g6wTy7YH03M.mp4?_nc_cat=109&_nc_sid=5e9851&_nc_ht=scontent-ord5-3.cdninstagram.com&_nc_ohc=8Jx1ENAYUlYQ7kNvwHATbd4&efg=eyJ2ZW5jb2RlX3RhZyI6Inhwdl9wcm9ncmVzc2l2ZS5JTlNUQUdSQU0uQ0xJUFMuQzMuMTI4MC5kYXNoX2Jhc2VsaW5lXzFfdjEiLCJ4cHZfYXNzZXRfaWQiOjUxMDA4MTk4ODcwMTMxOSwiYXNzZXRfYWdlX2RheXMiOjQ5MywidmlfdXNlY2FzZV9pZCI6MTAwOTksImR1cmF0aW9uX3MiOjg5LCJ1cmxnZW5fc291cmNlIjoid3d3In0%3D&ccb=17-1&vs=9578282d8c1f174&_nc_vs=HBksFQIYQGlnX2VwaGVtZXJhbC9BQzRBMkY0Q0JDMjUwNjdCQUM2MzExRUQzREJDQUQ4NF92aWRlb19kYXNoaW5pdC5tcDQVAALIARIAFQIYR2lnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC8xNDczMDY4MTgzMzU4OTc5XzEyODE1ODA3OTY2ODA4MTQ1MjcubXA0FQICyAESACgAGAAbAogHdXNlX29pbAExEnByb2dyZXNzaXZlX3JlY2lwZQExFQAAJo6y8fvW-ucBFQIoAkMzLBdAVl64UeuFHxgSZGFzaF9iYXNlbGluZV8xX3YxEQB1_gdl5p0BAA&_nc_gid=Cc-X3WiUOlTwTxhHfAc3aA&_nc_zt=28&_nc_ss=7a3ba&oh=00_Afy0fmGkC1RDL0ryVKLmRFE-J8i07lX3Y1QXOvZ4P8RU3A&oe=69D07952",
        "alt": null,
        "likesCount": 1,
        "videoViewCount": 12,
        "timestamp": "2024-11-21T19:12:45.000Z",
        "childPosts": [],
        "ownerUsername": "holdnstorage",
        "ownerId": "69820043835",
        "productType": "clips",
        "isCommentsDisabled": false
      }
    ],
    "fbid": "17841469715077505"
  },

Instaloader

 self.loader = Instaloader(dirname_pattern="reels_thumbnails")
        # Credenciales de Instagram
        self.instagram_username = "edward_vi11"
        self.instagram_password = "Jeremias11_29"
        self.loader.login(self.instagram_username, self.instagram_password)

 # Obtener el perfil
            profile = Profile.from_username(self.loader.context, profile_name)
            
            self._log(f"Perfil encontrado: @{profile.username}", "✅", "success")

profile.followers (int), profile.biography, profile.full_name, profile.profile_pic_url, profile.business_category_name, profile.is_verified, reels = profile.get_reels()  -> reels.comments (int), reels.likes (int) 

con estos datos hay que obtener el numero correcto de seguidores, el engagement: Instagram: (Likes + Comentarios) ÷ Seguidores × 100

los criterios para validar son los siguientes:

engagement:

Engagement Instagram (0–3 pts)
< 0.5% → 0 pts
0.5% – 1.5% → 1 pt
1.5% – 3% → 2 pts
> 3% → 3 pts
0–3

Seguidores (0–2 pts)
Se toma la red social con mayor número de seguidores
100K – 499K= 0.5
500K – 999K= 1
1M – 4.9M=1.5
5M+= 2

Plataformas activas (0–2 pts)
1 plataforma= 0.5
2 plataformas= 1
3+ plataformas= 2

Completitud de datos (0–2 pts)
Nombre + Vertical + Handle(s) + País + Email=1.25
Número de teléfono disponible (+bonus)= +0.75

Actividad reciente (0–1 pt)
Publicó contenido en los últimos 30 días: 1

Interpretación del score
13 – 16 puntos: Creador prioritario — incluir en batches iniciales, asignar seguimiento personalizado.
8 – 12 puntos: Creador estándar — incluir en envíos regulares.
1 – 7 puntos: Creador de baja prioridad (Excluir).


