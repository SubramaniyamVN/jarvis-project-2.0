import pyttsx3
import speech_recognition as sr

engine = pyttsx3.init()

def speak(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print("You said:", query)
    except Exception as e:
        print("Say that again...")
        return ""

    return query.lower()

def wish_me():
    speak("Hello sir, I am Jarvis. Ready to assist you.")