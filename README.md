# XG THUNDER - Free Fire EAT Token to Access Token / JWT Generator

Website: **http://localhost:8000/**

## Features
- EAT token se **Access Token** aur **JWT Token** nikaalo
- **Player profile photo** (avatar) + **banner** image dikhta hai
- Google / Facebook / Apple / X / VK se Garena login
- Killer Sharma jaisa cyber/glassmorphism design
- Social links (Telegram, Discord, YouTube, Instagram)
- Terms & Conditions modal

## Kaise Chalao (Windows)

1. Python 3 install hona chahiye (https://python.org)
2. Is folder me terminal/open karo
3. Ye command chalao:
   ```
   python server.py
   ```
4. Browser me kholo: http://localhost:8000/

## Kaise Use Kare
1. Neeche kisi provider (Google/Facebook/Apple/X/VK) se Garena login karo
2. Login ke baad browser history me `?eat=` ya `ticket.kiosgamer.co.id` ya `discstore.recargajogo.com.br` wali URL dhundho
3. Pura URL (ya sirf EAT token) text box me paste karo
4. **GENERATE ACCESS** button dabao
5. Access Token, JWT Token, profile photo aur banner sab dikh jayega

## Files
- `index.html` - website frontend (design + logic)
- `server.py` - Python server (CORS proxy for 3rd-party APIs)

## Note
Sirf educational/private use ke liye. Garena ke Terms & Conditions violate mat karo.
