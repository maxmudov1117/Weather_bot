import requests

# API ma'lumotlari
API_KEY = '5af718916f321b457560be9c34e12301'  # OpenWeatherMap dan olingan API kaliti
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'

# Foydalanuvchidan shahar nomini so'rash
city = input("Shahar nomini kiriting: ")

# API so'rovi
response = requests.get(BASE_URL, params={'q': city, 'appid': API_KEY, 'units': 'metric'})

if response.status_code == 200:
    data = response.json()
    # Ob-havo ma'lumotlarini chiqarish
    print(f"Shahar: {data['name']}")
    print(f"Temperatura: {data['main']['temp']}°C")
    print(f"Ob-havo: {data['weather'][0]['description']}")
else:
    print("Shahar topilmadi!")
