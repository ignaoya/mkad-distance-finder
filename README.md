# MKAD Distance Finder

This project is a Flask Blueprint API that allows you to search the distance from a given address to the Moscow Ring Road (MKAD).
It is implemented as a REST API with Flask_Restful, using a single GET endpoint.

The project includes a barebones Flask App in `app.py` which registers the `mkad_blueprint` defined in the mkad_blueprint module.
The test suites are all contained in `tests.py`.

To convert the given address into a set of coordinates, the project uses the Yandex Geocoder API. It also uses the geopy library
as a fallback method in case the Yandex API fails or the user doesn't have a Yandex API key available.

In order to determine the shortest distance from the given point to the MKAD, I've provided three different methods that can be
used alternatively. The first method uses a brute force search that compares the distances to all of the given kilometer 
coordinates of the MKAD and returns the distance to the closest one. The second method uses the shapely library in order to
search the closest point from the given address to the polygon formed by the MKAD and returns the distance to that point.
The third method is an alteration of the binary search algorithm that greatly reduces the amount of calculations needed to
find the closest point to the given address and would scale well if the objective was replaced with a much larger geographical
surface compared with the brute force algorithm. All three of these functions use the geopy.distance.distance() function in
order to measure geographic distances between coordinates.

The project is dockerized with two separate sets of dockerfiles and docker-compose files, one set to run the application, another
set to run the tests.

# Instructions

- Clone repository
- Add your Yandex API key to the .env file.
- Run `docker-compose up --build`
- You can now use the API.
- Request format: localhost:5000/mkad?address=[your_address]
- Request example: localhost:5000/mkad?address=2+15th+St+NW,+Washington,+DC+20024,+United%20States

# Running Tests

- Run `docker-compose -f docker-compose-test.yml up --build`
