# IMDb API
This is a REST API that serves details of top 250 movies fetched from IMDb website. The movies can be searched based on Name / Description or they can be sorted based on duration/name/release date/ rating.

### Details Fetched:
- Title (Name)
- Summary (Description)
- Rank
- Rating
- Duration
- Release Date

# Demo on Youtube:
demo execution video is available at : https://youtu.be/d9zeXq-qmp8

# Features:	
	- Fetch all 250 movie details (http://localhost:5000/movies/all)
		. sorted by Duration
			http://localhost:5000/movies/all?sortBy=duration
			http://localhost:5000/movies/all?sortBy=duration&desc=1
			
		. sorted by Name
			http://localhost:5000/movies/all?sortBy=name
			http://localhost:5000/movies/all?sortBy=name&desc=1
			
		. sorted by Release Date
			http://localhost:5000/movies/all?sortBy=releaseDate
			http://localhost:5000/movies/all?sortBy=releaseDate&desc=1
			
		. sorted by Rating
			http://localhost:5000/movies/all?sortBy=rating
			http://localhost:5000/movies/all?sortBy=rating&desc=1
		
	- Fetch movie details based on search
		. searched by Name
			http://localhost:5000/movie?name=godfather 
			
		. searched by Description
			http://localhost:5000/movie?desc=machine
			
# Authentication:
- bearerToken=*USERID*  as header of request
- Add user
		http://localhost:5000/addUser?userName=abcd

# Architecture

 ![here](https://github.com/Smiley-nrk/IMDb-API/blob/master/finalArch.png?raw=true)
 
# Implementation Detail
The implementation is done in Python language using BeautifulSoup and Requests for scraping.
For database, MongoDB is used.
For message queue, RabbitMQ is used.

Firstly, list of top 250 movies is available at: https://www.imdb.com/chart/top?ref_=nv_mv_250 .
But, some of the attributes of movie are not available on this page. For those, we have to check movie specific page.
This, in terms of scraping, means that 251 HTTP/s requests are needed. Which makes the actual process slow. So, first decision is to not visit 251 requests for each API call. Instead, store data in DB at some interval and then serve from DB only.
Now, when to update DB data?
For that, on every API call, only send 1 HTTP/s request to IMDb and scrap the list of movie rank and title. Compare that to data in DB. If both are inconsistent, then we need to update data stored in DB. For that also, we use RabbitMQ to communicate between DBService and Scraper Service.

# Flow chart:
The rough flow chart is available [here](https://github.com/Smiley-nrk/IMDb-API/blob/master/APIAndSraperFlow.pdf?raw=true)

# Helpful Links:
- BeautifulSoup documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Requests documentation: https://requests.readthedocs.io/en/master/
- Install RabbitMQ in local system: https://www.rabbitmq.com/download.html
- Connect and send message to & Read message from RabbitMQ: https://www.rabbitmq.com/tutorials/tutorial-one-python.html
- pymongo:
	https://api.mongodb.com/python/current/tutorial.html	
	https://www.w3schools.com/python/python_mongodb_getstarted.asp
- Flask to provide rest endpoints: https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask

- Useful Reads:
	https://medium.com/ryans-dev-notes/learning-rabbitmq-3f59d11f66b4
	https://dzone.com/articles/getting-started-with-rabbitmq-python-1
	http://jacobbridges.github.io/post/web-scraping-threads-and-queues/