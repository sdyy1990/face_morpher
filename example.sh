#!/bin/bash
wget "https://vignette.wikia.nocookie.net/gameofthrones/images/1/17/Jon-Snow-Kit-Harington_510.jpeg" -O snow.jpeg
wget "https://www.hbo.com/content/dam/hbodata/series/game-of-thrones/character/s5/daenarys-1920.jpg/_jcr_content/renditions/cq5dam.web.1200.675.jpeg" -O targ.jpg
convert snow.jpeg -resize 800 -crop 200x300+420+50 snow.jpg
convert targ.jpg -resize 800 -crop 200x300+280+50 targ0.jpg
mkdir -p output
mkdir -p outputp
python facemorpher/morpher.py --src=snow.jpg --dest=targ0.jpg --num=10 --out_frames=output
python facemorpher/morpher.py --src=snow.jpg --dest=targ0.jpg --num=10 --dots --tri --out_frames=outputp
convert -delay 10 ./output/frame0*.png -loop 0 animated.gif
convert -delay 10 ./outputp/frame0*.png -loop 0 animatedpoints.gif

