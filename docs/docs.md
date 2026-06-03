
This app is 24/7 automated. That's not marketing speak, that's literally what it does. You start it and it runs forever. Prices, charts, news, Japanese voice, YouTube stream — all handled automatically. If something breaks it fixes itself. That's the requirement, that's what was built.

Now the stream key question. seems you, think that every time the app reconnects to YouTube it needs a fresh key. That's not how it works at all.

The app uses ONE key. The same key. Forever. Well, not literally forever, but it doesn't expire on its own. When you see "FFmpeg died — restarting stream" in the logs, it's using the exact same key it loaded when you first started the program. It's just reconnecting. Like when your phone drops WiFi and reconnects — same password, same network.

When do you actually need a new key?

- You're doing YouTube Scheduled Events where every broadcast gets its own key. In that case yeah, you need a new one each time.
- You went into YouTube Studio and manually reset the key for security. Obviously the old one doesn't work anymore.
- Someone leaked the key or it got compromised somehow.

That's it. Network issues? Same key. Crash? Same key. YouTube kicked you off? Same key. The app is designed around this.

But here's the thing — if you DO need to change the key, you can't just edit the .env file while it's running. The app doesn't watch that file. You have to stop the whole thing and start it again. That's a limitation, not a bug. We can add hot-reloading later if needed but it wasn't in scope.

Also there's no YouTube API integration right now. The app can't create events, can't grab keys automatically, can't do any of that fancy stuff. It just reads the key from .env and uses it. Simple as that.

So my advice: use a normal Stream Now key, put it in .env, start the app, and don't touch it. That's the workflow this was built for. If they absolutely need scheduled events with unique keys every time, that's going to require manual steps (copy key, paste into .env, restart app) which breaks the whole 24/7 automation thing. We CAN build YouTube API automation for that but it's extra work.

To summarize for the client meeting:
- 24/7 unattended operation? Yes.
- Key expires automatically? No.
- App gets new key on reconnect? No, same key.
- Need new keys continuously? Only for scheduled events or manual rotation.
- Can change key without restart? No.


