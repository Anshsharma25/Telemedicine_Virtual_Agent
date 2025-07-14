# book_appointment.py

import random
from Database.doctor_data import doctors

def show_available_doctors():
    print("\n📋 Available Doctors Today:\n")
    for doc in doctors:
        print(f"👨‍⚕️ {doc['name']} ({doc['specialty']})")
        print(f"🏥 {doc['hospital']}")
        print(f"📅 Available: {'✅ Yes' if doc['available'] else '❌ No'}")
        if doc['available']:
            print(f"🕒 Slots: {', '.join(doc['slots'])}")
            print(f"📲 To Book: Type Doctor ID (e.g., {doc['id']}) and slot time (e.g., 11:30 AM)")
        else:
            print("🕒 No slots today.")
        print("-" * 50)

def book_appointment(doctor_id, slot):
    for doc in doctors:
        if doc["id"] == doctor_id:
            if not doc["available"]:
                return f"❌ {doc['name']} is not available today."
            if slot not in doc["slots"]:
                return f"❌ Slot '{slot}' is not available for {doc['name']}."
            booking_id = f"BKX{random.randint(1000, 9999)}"
            return f"✅ Appointment booked with {doc['name']} at {slot}.\n📄 Booking ID: {booking_id}"
    return "❌ Invalid Doctor ID."
