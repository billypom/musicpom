#!/usr/bin/env bash
# creates a 5 second long empty mp3 file
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 5 -q:a 9 -acodec libmp3lame out.mp3
