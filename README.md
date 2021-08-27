# mkad-distance-finder
This project is a Flask Blueprint API that allows you to search the distance from a given address to the Moscow Ring Road (MKAD).


# INSTRUCTIONS:

- Clone repository
- Add your Yandex API key to the .env file.
- Run `docker-compose up --build`
- You can now use the API.
- Request format: localhost:5000/mkad?address=[your_address]
- Request example: localhost:5000/mkad?address=2+15th+St+NW,+Washington,+DC+20024,+United%20States
