# movie_bot
made a discord bot that keeps track of the movies that my friends and I watch together. DB and bot are hosted locally on my home pc. 

bot comamnds:
1) /add "movie name"
  adds movie title, as well ping the imdb api to get the movie id, user who added it, time it was added, to the database.
2) /check "movie"
  check the database if a movie is in the list
3) /list
  display all movies that are on the list that havent been watched yet
4) /watched_list
   all movies that have been watched
5) /list_imdb
  all movies that havent been watched with a link to their imdb page
6) complete_list
   ever movie on the list
7) /random
  picks a movie from the list, true random
8) /random_by_user "@user @user2 @user3"
  picks a movie given a user tagged in the command
9) /remove
  after watching movie, this will set the movie to watch has true and not be displayed from /list
