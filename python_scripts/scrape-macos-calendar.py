#!/usr/bin/env python3
from Foundation import NSDate, NSCalendar
from EventKit import (EKEventStore, EKEntityTypeEvent,
                    EKSpanThisEvent)
from datetime import datetime, timedelta
import argparse
import re
import time
import csv

def wait_for_calendar_access():
   store = EKEventStore.alloc().init()
   access_granted = False
   
   def completion_handler(granted, error):
       nonlocal access_granted
       access_granted = granted
       print(f"Zugriff gewährt: {granted}")
       if error:
           print(f"Fehler: {error}")
   
   store.requestAccessToEntityType_completion_(
       EKEntityTypeEvent,
       completion_handler
   )
   time.sleep(2)
   return store

def get_events(search_pattern, start_date=None, end_date=None):
   store = wait_for_calendar_access()
   print("EventStore initialisiert")
   
   start = start_date or datetime.now()
   end = end_date or (start + timedelta(days=7))
   print(f"Suche Termine von {start} bis {end}")
   
   ns_start = NSDate.dateWithTimeIntervalSince1970_(start.timestamp())
   ns_end = NSDate.dateWithTimeIntervalSince1970_(end.timestamp())
   
   # Alle Kalender holen
   calendars = store.calendarsForEntityType_(EKEntityTypeEvent)
   
   # Events aus allen Kalendern holen
   all_events = []
   for calendar in calendars:
       try:
           predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
               ns_start, ns_end, [calendar])
           events = store.eventsMatchingPredicate_(predicate)
           print(f"Kalender '{calendar.title()}': {len(events)} Events gefunden")
           all_events.extend(events)
       except Exception as e:
           print(f"Fehler beim Lesen der Events aus {calendar.title()}: {e}")
   
   pattern = re.compile(search_pattern, re.IGNORECASE) if search_pattern else None
   
   found_events = []
   for event in all_events:
       if pattern is None or pattern.search(str(event.title())):
           event_start = datetime.fromtimestamp(
               event.startDate().timeIntervalSince1970())
           found_events.append({
               'title': event.title(),
               'date': event_start.strftime('%m/%d/%Y'),
               'time': event_start.strftime('%H:%M'),
               'location': event.location() or 'Kein Ort'
           })
   
   return sorted(found_events, key=lambda x: f"{x['date']} {x['time']}")

def write_csv(events, filename='out.csv'):
   with open(filename, 'w', newline='', encoding='utf-8') as f:
       writer = csv.DictWriter(f, fieldnames=['title', 'date', 'time', 'location'])
       writer.writeheader()
       writer.writerows(events)
   print(f"\nErgebnisse wurden in {filename} gespeichert")

def main():
   parser = argparse.ArgumentParser(description='Durchsuche Kalendereinträge')
   parser.add_argument('--pattern', help='Suchbegriff (regulärer Ausdruck)', default=None)
   parser.add_argument('--days', type=int, help='Anzahl der Tage ab heute', default=7)
   args = parser.parse_args()

   start_date = datetime.now()
   end_date = start_date + timedelta(days=args.days)

   events = get_events(args.pattern, start_date, end_date)
   if events:
       print(f"\nGefundene Termine: {len(events)}")
       write_csv(events)
   else:
       print("Keine Termine gefunden.")

if __name__ == "__main__":
   main()