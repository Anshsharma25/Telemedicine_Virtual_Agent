# telemed_connect_agent.py

import json
from twilio.rest import Client
from uuid import uuid4

# Twilio Config (replace with your actual credentials)
TWILIO_SID = 'your_twilio_account_sid'
TWILIO_AUTH = 'your_twilio_auth_token'
TWILIO_PHONE = '+1234567890'  # Your Twilio phone number

client = Client(TWILIO_SID, TWILIO_AUTH)

def ask_user_yes_no():
    response = input("Do you want to connect with a real-time doctor? (yes/no): ")
    return response.lower().strip() in ['yes', 'y']

def get_user_phone():
    phone = input("Please enter your phone number with country code: ")
    if phone.startswith('+') and len(phone) > 10:
        return phone
    print("Invalid phone number. Try again.")
    return get_user_phone()

def get_available_doctor():
    with open("doctors.json", "r") as file:
        doctors = json.load(file)
    for doctor in doctors:
        if doctor['status'] == 'available':
            return doctor
    return None

def generate_meet_link():
    return f"https://meet.jit.si/telemed-{uuid4()}"

def send_meet_sms(to_phone, link):
    message = client.messages.create(
        body=f"Doctor is ready. Join here: {link}",
        from_=TWILIO_PHONE,
        to=to_phone
    )
    print(f"Sent link to {to_phone}")

def main():
    print("\n📞 Welcome to the Telemedicine Assistant 📞")
    if not ask_user_yes_no():
        print("Okay, feel free to reach out anytime. Goodbye!")
        return

    patient_phone = get_user_phone()
    print("Looking for an available doctor...")

    doctor = get_available_doctor()
    if not doctor:
        print("❌ Sorry, no doctors are currently available. Try again later.")
        return

    print(f"✅ Doctor {doctor['name']} is available.")
    meet_link = generate_meet_link()

    # Send to both patient and doctor
    send_meet_sms(patient_phone, meet_link)
    send_meet_sms(doctor['phone'], meet_link)

    print("📲 A video link has been sent to both parties.")

if __name__ == "__main__":
    main()
