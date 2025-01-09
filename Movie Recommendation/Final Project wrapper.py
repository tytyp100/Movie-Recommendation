import sqlite3

#Function to create the tables needed
def create_tables():
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()

    #Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS User")
    cursor.execute("DROP TABLE IF EXISTS Movie")
    cursor.execute("DROP TABLE IF EXISTS Rating")
    cursor.execute("DROP TABLE IF EXISTS Watch_Status")
    cursor.execute("DROP TABLE IF EXISTS Genre")
    cursor.execute("DROP TABLE IF EXISTS Movie_Genre")

    #Create tables (Check ER Diagram)
    cursor.execute('''CREATE TABLE IF NOT EXISTS User (
                      user_id INTEGER PRIMARY KEY,
                      username TEXT NOT NULL,
                      password TEXT NOT NULL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Movie (
                      movie_id INTEGER PRIMARY KEY,
                      title TEXT NOT NULL,
                      director TEXT,
                      year INTEGER,
                      duration INTEGER)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Rating (
                      rating_id INTEGER PRIMARY KEY,
                      user_id INTEGER,
                      movie_id INTEGER,
                      score INTEGER CHECK(score >= 0 AND score <= 100),
                      recommend BOOLEAN,
                      comment TEXT,
                      FOREIGN KEY(user_id) REFERENCES User(user_id),
                      FOREIGN KEY(movie_id) REFERENCES Movie(movie_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Watch_Status (
                      user_id INTEGER,
                      movie_id INTEGER,
                      status TEXT,
                      PRIMARY KEY (user_id, movie_id),
                      FOREIGN KEY(user_id) REFERENCES User(user_id),
                      FOREIGN KEY(movie_id) REFERENCES Movie(movie_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Genre (
                      genre_id INTEGER PRIMARY KEY,
                      genre_name TEXT NOT NULL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Movie_Genre (
                      movie_id INTEGER,
                      genre_id INTEGER,
                      PRIMARY KEY (movie_id, genre_id),
                      FOREIGN KEY(movie_id) REFERENCES Movie(movie_id),
                      FOREIGN KEY(genre_id) REFERENCES Genre(genre_id))''')

    connection.commit()
    connection.close()

#Login so the program knows who's watchlist to show when choosing option 2
def login(username, password):
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    cursor.execute("SELECT user_id FROM User WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone() 
    connection.close()
    if result:
        print("Login successful!")
        return result[0]  
    else:
        print("Login failed. Invalid username or password.")
        return None

def view_movie_catalog():
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    cursor.execute("SELECT title, director, year, duration FROM Movie")
    movies = cursor.fetchall()
    connection.close()
    #print all the movies in the catalog
    if movies:
        print("Movie Catalog:")
        for movie in movies:
            title, director, year, duration = movie
            print(f"Title: {title}, Director: {director}, Year: {year}, Duration: {duration} mins")
    else:
        print("No movies available in the catalog.")

def view_user_watchlist(user_id, print_header=True):
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #Get the movie as long as the ratings that the user gave for that movie
    query = '''
        SELECT Movie.title, Watch_Status.status, 
               Rating.score, Rating.recommend, Rating.comment
        FROM Watch_Status
        JOIN Movie ON Watch_Status.movie_id = Movie.movie_id
        LEFT JOIN Rating ON Rating.user_id = Watch_Status.user_id 
                          AND Rating.movie_id = Watch_Status.movie_id
        WHERE Watch_Status.user_id = ?
    '''
    cursor.execute(query, (user_id,))
    watchlist = cursor.fetchall()
    connection.close()
    if print_header:
        print("User's Watchlist:")
    #return the information about the movies in the watchlist
    if watchlist:
        for title, status, score, recommend, comment in watchlist:
            score_display = score if score is not None else "N/A"
            recommend_display = "Yes" if recommend else "No" if recommend is not None else "N/A"
            comment_display = comment if comment is not None else "N/A"
            print(f"Title: {title}, Status: {status}, Score: {score_display}, Recommend: {recommend_display}, Comment: {comment_display}")
    else:
        print("Watchlist is empty.")

def add_to_watchlist(user_id):
    #Ask for movie title that the user wants to add
    movie_title = input("Enter the title of the movie to add to your watchlist: ")
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #Get movie_id for the movie title
    cursor.execute("SELECT movie_id FROM Movie WHERE title = ?", (movie_title,))
    movie = cursor.fetchone()
    if movie:
        movie_id = movie[0]
        #Get the watch_status of the movie (wacthed or plan to watch)
        while True:
            status = input("Set the status: (1) Watched or (2) Plan to Watch: ")
            if status == "1":
                #if watched, then ask for rating, recommendation and comment
                status = "Watched"
                score = int(input("Enter your rating score (0-100): "))
                recommend = input("Would you recommend this movie? (yes/no): ").strip().lower() == "yes"
                comment = input("Enter any comments for this movie: ") 
                # Insert the rating directly with user_id and movie_id
                cursor.execute("INSERT INTO Rating (user_id, movie_id, score, recommend, comment) VALUES (?, ?, ?, ?, ?)", 
                               (user_id, movie_id, score, recommend, comment))
                break
            elif status == "2":
                #if plan to watch, then just add the movie to the watchlist with status as plan to watch
                status = "Plan to Watch"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
        cursor.execute("INSERT INTO Watch_Status (user_id, movie_id, status) VALUES (?, ?, ?)", 
                       (user_id, movie_id, status))
        connection.commit()
        print(f"{movie_title} has been added to your watchlist with status: {status}.")
    else:
        print("Movie not found in the catalog.")
    connection.close()

def view_watchlist_by_username(username):
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #Get the user ID for the inputted username
    cursor.execute("SELECT user_id FROM User WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        print("User not found.")
    else:
        user_id = user[0]
        print(f"{username}'s Watchlist:")
        #Show the watchlist for the user
        view_user_watchlist(user_id, print_header=False)
    connection.close()

def search_movie_ratings():
    #Get movie title from user
    movie_title = input("Enter the title of the movie to view ratings: ")
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #Get movie ID for the title
    cursor.execute("SELECT movie_id FROM Movie WHERE title = ?", (movie_title,))
    movie = cursor.fetchone()
    if movie:
        movie_id = movie[0]   
        #Get all the ratings for the movie
        cursor.execute('''
            SELECT User.username, Rating.score, Rating.recommend, Rating.comment
            FROM Rating
            JOIN User ON Rating.user_id = User.user_id
            WHERE Rating.movie_id = ?
        ''', (movie_id,))
        ratings = cursor.fetchall()
        #Show the ratings
        if ratings:
            print(f"Ratings for {movie_title}:")
            for username, score, recommend, comment in ratings:
                recommend_text = "Yes" if recommend else "No"
                print(f"User: {username}, Score: {score}, Recommend: {recommend_text}, Comment: {comment}")
        else:
            print(f"No ratings found for {movie_title}.")
    else:
        print("Movie not found in the catalog.")
    connection.close()

def search_by_genre():
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #Shows the genre options
    cursor.execute("SELECT genre_id, genre_name FROM Genre")
    genres = cursor.fetchall()   
    print("Available Genres:")
    for genre_id, genre_name in genres:
        print(f"{genre_id}. {genre_name}")
    # Get the input for the genre ID 
    genre_id = input("Enter the Genre ID you want to search for: ")
    #Get all the movies in that genre
    query = '''
        SELECT Movie.title, Movie.director, Movie.year, Movie.duration
        FROM Movie
        JOIN Movie_Genre ON Movie.movie_id = Movie_Genre.movie_id
        WHERE Movie_Genre.genre_id = ?
    '''
    cursor.execute(query, (genre_id,))
    movies = cursor.fetchall()
    if movies:
        print("\nMovies in Selected Genre:")
        for title, director, year, duration in movies:
            print(f"Title: {title}, Director: {director}, Year: {year}, Duration: {duration} mins")
    else:
        print("No movies found in the selected genre.")
    connection.close()

def InitializeData():
    connection = sqlite3.connect("movie_recommendation.db")
    cursor = connection.cursor()
    #All the users
    users = [
        ("Tim", "password123"),
        ("Bob", "pass"),
        ("Joe", "joe123"),
        ("Sam", "sam"),
        ("Fred", "idk"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO User (username, password) VALUES (?, ?)", users)
    #All the movies
    movies = [
        ("Inception", "Christopher Nolan", 2010, 148),
        ("The Matrix", "Wachowskis", 1999, 136),
        ("Interstellar", "Christopher Nolan", 2014, 169),
        ("Parasite", "Bong Joon-ho", 2019, 132),
        ("The Godfather", "Francis Ford Coppola", 1972, 175),
        ("Pulp Fiction", "Quentin Tarantino", 1994, 154),
        ("The Shawshank Redemption", "Frank Darabont", 1994, 142),
        ("Fight Club", "David Fincher", 1999, 139),
        ("Forrest Gump", "Robert Zemeckis", 1994, 142),
        ("Rush Hour", "Brett Ratner", 1998, 98),
    ]
    cursor.executemany("INSERT OR IGNORE INTO Movie (title, director, year, duration) VALUES (?, ?, ?, ?)", movies)
    #Each user's watchlist
    watch_statuses = [
        #Tim's watchlist
        (1, 1, "Watched"),
        (1, 2, "Watched"),
        (1, 3, "Plan to Watch"),
        
        #Bob's watchlist
        (2, 4, "Watched"),
        (2, 5, "Watched"),
        (2, 6, "Plan to Watch"),
        
        #Joe's watchlist
        (3, 7, "Watched"),
        (3, 8, "Watched"),
        (3, 9, "Plan to Watch"),
        
        #Sam's watchlist
        (4, 10, "Watched"),
        (4, 1, "Watched"),
        (4, 2, "Plan to Watch"),
        
        #Fred's watchlist
        (5, 3, "Watched"),
        (5, 4, "Watched"),
        (5, 5, "Plan to Watch"),
    ]
    cursor.executemany("INSERT OR IGNORE INTO Watch_Status (user_id, movie_id, status) VALUES (?, ?, ?)", watch_statuses)
    
    #Ratings for each movie by each user
    ratings = [
        (1, 1, 85, True, "Amazing movie!"),  # Tim rating Inception
        (1, 2, 80, True, "Enjoyed it a lot."),  # Tim rating The Matrix
        (2, 4, 90, True, "Mind-blowing plot."),  # Bob rating Parasite
        (2, 5, 95, True, "Classic must-watch."),  # Bob rating The Godfather
        (3, 7, 75, True, "Good but a littl slow."),  # Joe rating Shawshank Redemption
        (3, 8, 85, True, "Fight scenes are incredible."),  # Joe rating Fight Club
        (4, 10, 95, True, "Funniest movie ever"),  # Sam rating Rush Hour
        (4, 1, 88, True, "Unique story."),  # Sam rating Inception
        (5, 3, 100, True, "My favourite movie of all time!"),  # Fred rating Interstellar
        (5, 4, 50, False, "Not my type of movie"),  # Fred rating Parasite
    ]
    cursor.executemany("INSERT OR IGNORE INTO Rating (user_id, movie_id, score, recommend, comment) VALUES (?, ?, ?, ?, ?)", ratings)

    #All genres
    genres = [
        ("Action",),
        ("Drama",),
        ("Sci-Fi",),
        ("Thriller",),
        ("Comedy",),
    ]
    cursor.executemany("INSERT OR IGNORE INTO Genre (genre_name) VALUES (?)", genres)
    
    #Genres for each movie
    movie_genres = [
        (1, 3),  # Inception - Sci-Fi
        (1, 4),  # Inception - Thriller
        (2, 3),  # The Matrix - Sci-Fi
        (3, 3),  # Interstellar - Sci-Fi
        (4, 4),  # Parasite - Thriller
        (5, 2),  # The Godfather - Drama
        (6, 2),  # Pulp Fiction - Drama
        (7, 2),  # The Shawshank Redemption - Drama
        (8, 2),  # Fight Club - Drama
        (9, 2),  # Forrest Gump - Drama
        (10, 1), # Rush Hour - Action
        (10, 5), # Rush Hour - Comedy
    ]
    cursor.executemany("INSERT OR IGNORE INTO Movie_Genre (movie_id, genre_id) VALUES (?, ?)", movie_genres)
    
    connection.commit()
    connection.close()
    print("Database initialized with sample data.")

def main():
    #create_tables()    <-- Uncomment this if you want to reset the data
    #InitializeData()    <-- Uncomment this if you want to reset the data
    user_id = None
    while user_id == None:
        username = input("Username: ")
        password = input("Password: ")
        user_id = login(username,password)
    while True:
        print("\n-----------------------------------------")
        print("Options:")
        print("1. Look at Movie catalog")
        print("2. View your Own Watchlist")
        print("3. Add to Watchlist")
        print("4. Search by genre")
        print("5. View other's watchlist")
        print("6. Search up movie ratings")
        print("7. Quit")
        
        choice = input("Choose an option: ")
        if choice == "1":
            view_movie_catalog()
        elif choice == "2":
            view_user_watchlist(user_id)
        elif choice == "3":
            add_to_watchlist(user_id)
        elif choice == "4":
            search_by_genre()
        elif choice == "5":
            u = input("Username of the user you want to view: ")
            view_watchlist_by_username(u)
        elif choice == "6":
            search_movie_ratings()
        elif choice == "7":
            break
        else:
            print("Invalid choice, Please try again!")

main()