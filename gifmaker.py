#!/usr/bin/env python3
import os
import sys
import glob
import imageio

def main():
    if len(sys.argv) != 5:
        print("Usage: {} <Verzeichnis> <Ausgabe.gif> <Frame-Dauer (ms)> <Last-Frame-Dauer (ms)>".format(sys.argv[0]))
        sys.exit(1)
    
    directory = sys.argv[1]
    output = sys.argv[2]
    try:
        frame_delay_ms = float(sys.argv[3])
        last_frame_delay_ms = float(sys.argv[4])
    except ValueError:
        print("Frame-Dauern müssen Zahlen sein.")
        sys.exit(1)
    
    # Dateien im Verzeichnis sammeln und nach Änderungsdatum sortieren (älteste zuerst)
    image_files = glob.glob(os.path.join(directory, "*"))
    image_files.sort(key=os.path.getmtime)
    
    if not image_files:
        print("Keine Bilder in", directory, "gefunden.")
        sys.exit(1)
    
    images = []
    durations = []
    
    # Alle Frames bis auf den letzten
    for file in image_files[:-1]:
        img = imageio.imread(file)
        images.append(img)
        durations.append(frame_delay_ms / 1000.0)
    
    # Letzter Frame mit längerer Standzeit (ohne Duplizieren)
    last_img = imageio.imread(image_files[-1])
    images.append(last_img)
    durations.append(last_frame_delay_ms / 1000.0)
    
    # GIF erstellen (loop=0 => Endlosschleife)
    imageio.mimsave(output, images, duration=durations, loop=0)
    print("GIF erstellt:", output)

if __name__ == "__main__":
    main()